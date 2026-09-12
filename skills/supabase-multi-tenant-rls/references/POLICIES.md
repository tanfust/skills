# Policy patterns by table type

Read the section matching the table being worked on. All patterns assume the helper functions from SKILL.md exist.

- [Plain tenant table](#plain-tenant-table)
- [Rows owned by one member inside an org](#rows-owned-by-one-member-inside-an-org)
- [Soft-deleted rows](#soft-deleted-rows)
- [Public-readable rows inside a tenant table](#public-readable-rows-inside-a-tenant-table)
- [Memberships](#memberships)
- [Invites](#invites)
- [Storage objects](#storage-objects)
- [Views](#views)
- [Realtime](#realtime)

## Plain tenant table

The default. Any member reads and writes, admins delete.

```sql
alter table public.projects enable row level security;
create index projects_org_id_idx on public.projects (org_id);

create policy "members read"   on public.projects for select to authenticated
  using (public.is_org_member(org_id));

create policy "members insert" on public.projects for insert to authenticated
  with check (public.is_org_member(org_id));

create policy "members update" on public.projects for update to authenticated
  using (public.is_org_member(org_id))
  with check (public.is_org_member(org_id));

create policy "admins delete"  on public.projects for delete to authenticated
  using (public.has_org_role(org_id, array['owner','admin']::public.org_role[]));
```

## Rows owned by one member inside an org

Notes, drafts, personal API keys. Visible to the author, plus admins if the product needs oversight.

```sql
create policy "author reads own" on public.notes for select to authenticated
  using (
    public.is_org_member(org_id)
    and (
      author_id = (select auth.uid())
      or public.has_org_role(org_id, array['owner','admin']::public.org_role[])
    )
  );

-- The with check pins the author to the caller, so a row cannot be
-- inserted or re-assigned under someone else's name.
create policy "author writes own" on public.notes for insert to authenticated
  with check (public.is_org_member(org_id) and author_id = (select auth.uid()));

create policy "author updates own" on public.notes for update to authenticated
  using  (author_id = (select auth.uid()) and public.is_org_member(org_id))
  with check (author_id = (select auth.uid()) and public.is_org_member(org_id));
```

## Soft-deleted rows

Put the filter in the policy rather than trusting every client query to remember `.is('deleted_at', null)`. Keep a separate admin policy for the restore view instead of weakening the main one.

```sql
create policy "members read live rows" on public.documents for select to authenticated
  using (public.is_org_member(org_id) and deleted_at is null);

create policy "admins read deleted rows" on public.documents for select to authenticated
  using (public.has_org_role(org_id, array['owner','admin']::public.org_role[]));
```

Two permissive SELECT policies are OR-ed together, which is what is wanted here: admins see both sets.

## Public-readable rows inside a tenant table

A published page, a shared link. The tempting version grants `to anon` on the whole table with a `published = true` predicate. That works, but it also exposes every column, including internal notes and the author's user id.

Prefer a view with `security_invoker` off, owned by a role with narrow access, exposing only the public columns. Or a `security definer` RPC returning a typed row. Either way, keep the base table closed to `anon`.

```sql
create view public.published_pages
with (security_invoker = off) as
  select id, org_id, slug, title, body_html, published_at
  from public.pages
  where published = true;

grant select on public.published_pages to anon, authenticated;
```

This is the one place where `security_invoker = off` is deliberate. Everywhere else it is a bug, and the audit flags it.

## Memberships

The table that guards every other table. Read is open to the org, write is owner-only, and the destructive rules live in triggers because policies cannot count rows.

```sql
alter table public.memberships enable row level security;

create policy "members see the roster" on public.memberships for select to authenticated
  using (public.is_org_member(org_id));

create policy "owners add members" on public.memberships for insert to authenticated
  with check (public.has_org_role(org_id, array['owner']::public.org_role[]));

-- Note the absence of "or user_id = auth.uid()" in using. Self-service
-- role changes are exactly the hole this policy exists to close.
create policy "owners change roles" on public.memberships for update to authenticated
  using  (public.has_org_role(org_id, array['owner']::public.org_role[]))
  with check (public.has_org_role(org_id, array['owner']::public.org_role[]));

create policy "owners remove members" on public.memberships for delete to authenticated
  using (public.has_org_role(org_id, array['owner']::public.org_role[]));

-- Leaving voluntarily is a separate, narrower policy.
create policy "members remove themselves" on public.memberships for delete to authenticated
  using (user_id = (select auth.uid()));
```

Then the rule policies cannot express:

```sql
create or replace function public.prevent_last_owner_removal()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if (old.role = 'owner') then
    if (select count(*) from public.memberships
        where org_id = old.org_id and role = 'owner') <= 1 then
      raise exception 'organization must retain at least one owner';
    end if;
  end if;
  return old;
end;
$$;

create trigger memberships_protect_last_owner
  before delete or update of role on public.memberships
  for each row execute function public.prevent_last_owner_removal();
```

## Invites

No permissive policy for `anon`. Everything goes through two RPCs.

```sql
create table public.invites (
  id          uuid primary key default gen_random_uuid(),
  org_id      uuid not null references public.organizations(id) on delete cascade,
  email       text not null,
  role        public.org_role not null default 'member',
  token_hash  text not null unique,          -- never the raw token
  expires_at  timestamptz not null,
  accepted_at timestamptz,
  created_by  uuid not null references auth.users(id),
  created_at  timestamptz not null default now()
);

alter table public.invites enable row level security;

create policy "admins manage invites" on public.invites for all to authenticated
  using  (public.has_org_role(org_id, array['owner','admin']::public.org_role[]))
  with check (public.has_org_role(org_id, array['owner','admin']::public.org_role[]));
```

Lookup, callable while signed out, returning the minimum:

```sql
create or replace function public.peek_invite(raw_token text)
returns table (org_name text, role public.org_role)
language sql
stable
security definer
set search_path = ''
as $$
  select o.name, i.role
  from public.invites i
  join public.organizations o on o.id = i.org_id
  where i.token_hash = encode(extensions.digest(raw_token, 'sha256'), 'hex')
    and i.accepted_at is null
    and i.expires_at > now();
$$;

revoke execute on function public.peek_invite(text) from public;
grant  execute on function public.peek_invite(text) to anon, authenticated;
```

Acceptance, atomic, signed-in only:

```sql
create or replace function public.accept_invite(raw_token text)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_invite public.invites;
begin
  if (select auth.uid()) is null then
    raise exception 'authentication required';
  end if;

  select * into v_invite
  from public.invites
  where token_hash = encode(extensions.digest(raw_token, 'sha256'), 'hex')
    and accepted_at is null
    and expires_at > now()
  for update;

  if not found then
    raise exception 'invite is invalid or has expired';
  end if;

  insert into public.memberships (org_id, user_id, role)
  values (v_invite.org_id, (select auth.uid()), v_invite.role)
  on conflict (org_id, user_id) do nothing;

  update public.invites set accepted_at = now() where id = v_invite.id;

  return v_invite.org_id;
end;
$$;

revoke execute on function public.accept_invite(text) from public, anon;
grant  execute on function public.accept_invite(text) to authenticated;
```

The `for update` lock is what stops two simultaneous redemptions of the same link.

## Storage objects

Bucket policies are ordinary RLS policies on `storage.objects`. Put the org id in the path as the first segment and match on it, because `storage.foldername()` is the only tenant signal available at that layer.

```sql
create policy "members read org files"
  on storage.objects for select to authenticated
  using (
    bucket_id = 'org-files'
    and public.is_org_member(((storage.foldername(name))[1])::uuid)
  );

create policy "members upload org files"
  on storage.objects for insert to authenticated
  with check (
    bucket_id = 'org-files'
    and public.is_org_member(((storage.foldername(name))[1])::uuid)
  );
```

The cast throws if the first path segment is not a uuid, which is the desired outcome for a malformed upload path. Keep the bucket private; a public bucket ignores all of this.

## Views

Create every view with `security_invoker = on` so the caller's policies apply to the underlying tables. The only exception is the deliberate public-projection case above.

```sql
create view public.project_summaries
with (security_invoker = on) as
  select p.id, p.org_id, p.name, count(t.id) as task_count
  from public.projects p
  left join public.tasks t on t.project_id = p.id
  group by p.id;
```

## Realtime

Realtime respects RLS on the source table for `postgres_changes`, but the subscription still needs the table added to the publication, and the client still needs to filter by `org_id` to avoid receiving events it will then be denied. Adding a table to `supabase_realtime` without RLS enabled broadcasts every change to every subscriber.

```sql
alter publication supabase_realtime add table public.tasks;
```

Check the publication membership during the audit, not after the first leak.
