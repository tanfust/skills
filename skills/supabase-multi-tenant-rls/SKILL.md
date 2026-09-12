---
name: supabase-multi-tenant-rls
description: Design, implement and verify multi-tenant Row Level Security in Supabase Postgres - organizations, memberships, roles and invites - without recursive policies, privilege escalation, or silent cross-tenant leaks. Use this whenever the work touches organizations, teams, workspaces, tenants, members, invites, roles and permissions, RLS policies, security definer helper functions, or any table carrying an org_id or tenant_id. Use it for audits and debugging of existing policies too. Reach for it even when the request sounds like a trivial "just add a policy" task, because the failure mode here is silent: a wrong policy returns rows instead of an error.
---

# Multi-tenant RLS on Supabase

Most RLS mistakes do not throw. They return the wrong rows, or accept a write that should have been rejected, and nobody notices until a customer sees another customer's data. So the work is not finished when the policy is written. It is finished when a cross-tenant read has been proven to return zero rows.

This skill covers the org / membership / role shape used by B2B SaaS. For single-user-owns-the-row apps, a policy of `user_id = (select auth.uid())` is enough and none of this is needed.

## Order of work

Follow this order. Each step depends on the one before it, and the verification step is not optional.

1. Fix the tenancy shape
2. Write the schema declaratively
3. Write the helper functions
4. Write the policies, per table, per command
5. Handle the two dangerous tables: memberships and invites
6. Run the audit and the cross-tenant test

## 1. Fix the tenancy shape

Answer these before writing SQL, because changing them later means rewriting every policy:

- Can a user belong to more than one organization? (Usually yes. If yes, the org cannot live on the user row.)
- Is there a role hierarchy, and what is the minimum set? Start with `owner`, `admin`, `member`. Do not build per-resource permissions until a customer asks.
- Can an organization contain sub-units (projects, teams) with their own access rules? If yes, decide now whether policies check org membership or unit membership. Mixing both later produces policies nobody can reason about.

**Carry `org_id` on every tenant table, denormalized.** Resist normalizing it away. A policy that joins through two tables to find the tenant runs that join on every row of every query, and it is the single most common cause of a Supabase app that is fast in development and unusable at 100k rows.

## 2. Write the schema declaratively

Author the schema as declarative files under `supabase/schemas/`, then generate the migration:

```bash
supabase db diff -f add_organizations
```

This keeps the current state readable in one place instead of reconstructing it from thirty migration files. The generated migration is what ships; review it before committing, because `db diff` will happily generate a destructive change if a column was renamed.

Minimum shape:

```sql
create type public.org_role as enum ('owner', 'admin', 'member');

create table public.organizations (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  slug        text unique not null,
  created_at  timestamptz not null default now()
);

create table public.memberships (
  org_id      uuid not null references public.organizations(id) on delete cascade,
  user_id     uuid not null references auth.users(id) on delete cascade,
  role        public.org_role not null default 'member',
  created_at  timestamptz not null default now(),
  primary key (org_id, user_id)
);

-- The index that makes every policy fast. The primary key covers (org_id, user_id);
-- this covers the other direction, which is how the helper functions look it up.
create index memberships_user_id_org_id_idx on public.memberships (user_id, org_id);
```

Every tenant table then carries `org_id uuid not null references public.organizations(id) on delete cascade` and an index on it.

## 3. Write the helper functions

A policy on `memberships` that queries `memberships` causes infinite recursion (Postgres error 42P17). The way out is a `security definer` function, which runs as its owner and therefore skips RLS on the tables it touches.

Security definer functions are the sharpest tool in this skill. Every one of them needs all four of the following, and the audit in step 6 checks for exactly this:

```sql
create or replace function public.is_org_member(target_org uuid)
returns boolean
language sql
stable                    -- not volatile: lets the planner evaluate once per statement
security definer          -- bypasses RLS, which is the point
set search_path = ''      -- see below
as $$
  select exists (
    select 1
    from public.memberships m   -- fully qualified, because search_path is empty
    where m.org_id = target_org
      and m.user_id = (select auth.uid())
  );
$$;

revoke execute on function public.is_org_member(uuid) from public, anon;
grant  execute on function public.is_org_member(uuid) to authenticated;
```

Why each line matters:

- **`set search_path = ''`** with fully qualified table names. Without it, anyone who can create objects in a schema on the search path can shadow `memberships` with their own table, and the function will happily read it while running as the owner. This is the standard escalation path through a security definer function.
- **`revoke execute ... from public`**. Postgres grants EXECUTE on new functions to PUBLIC by default. A security definer function left at the default is an RLS bypass that any anonymous caller can invoke through the REST API. Revoke first, then grant narrowly.
- **`stable`**, so the result is cached within the statement rather than recomputed per row.

Add a role-aware variant for anything that is not a plain read:

```sql
create or replace function public.has_org_role(target_org uuid, allowed public.org_role[])
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.memberships m
    where m.org_id = target_org
      and m.user_id = (select auth.uid())
      and m.role = any(allowed)
  );
$$;

revoke execute on function public.has_org_role(uuid, public.org_role[]) from public, anon;
grant  execute on function public.has_org_role(uuid, public.org_role[]) to authenticated;
```

## 4. Write the policies

Three rules, applied to every table without exception.

**Name the role.** A policy without `to authenticated` also runs for `anon`, which means the anon key evaluates it on every request.

**Split by command.** Write separate `for select`, `for insert`, `for update`, `for delete` policies rather than one `for all`. The semantics differ per command and `for all` hides that.

**Wrap `auth.uid()` in a scalar subquery.** `(select auth.uid())` is evaluated once as an InitPlan; a bare `auth.uid()` is re-evaluated per row.

```sql
alter table public.documents enable row level security;

create policy "members read org documents"
  on public.documents for select to authenticated
  using (public.is_org_member(org_id));

create policy "members create org documents"
  on public.documents for insert to authenticated
  with check (public.is_org_member(org_id));

create policy "members update org documents"
  on public.documents for update to authenticated
  using (public.is_org_member(org_id))
  with check (public.is_org_member(org_id));   -- both, see below

create policy "admins delete org documents"
  on public.documents for delete to authenticated
  using (public.has_org_role(org_id, array['owner', 'admin']::public.org_role[]));
```

**The UPDATE trap.** `using` decides which rows may be updated. `with check` decides what they may be updated *to*. An UPDATE policy with only `using` lets a member take a row they legitimately own and set `org_id` to another organization, moving data across the tenant boundary with one PATCH. Every UPDATE policy needs both clauses.

**Enabling RLS is separate from writing policies, and granting is separate from both.** A table with RLS enabled and no policies denies everything, which is a safe failure. A table with *no* RLS enabled is fully readable through the Data API by anyone holding the anon key, which is not. Newly created tables are also not automatically exposed to the Data API depending on project settings; if a table needs to be reachable, the `authenticated` role needs an explicit grant. Check all three.

See `references/POLICIES.md` for the per-table-type patterns: owner-scoped rows, soft-deleted rows, cross-org shared resources, storage objects, and views.

## 5. The two dangerous tables

**`memberships`** is where privilege escalation lives. The rows in it are the input to every other policy in the database, so a permissive UPDATE here unlocks everything else.

- A member must not be able to change their own `role`. The UPDATE policy needs a `with check` that the caller holds `owner` or `admin`, and the `using` clause must not be satisfied by "this is my row".
- An admin must not be able to promote themselves to owner, or demote an owner.
- The last owner of an organization must not be removable. Enforce this in a trigger, not a policy. Policies see one row at a time and cannot count the survivors.

**`invites`** is read by people who are not yet members, and often do not yet have an account. Do not solve this with a permissive policy on the table.

- Store a hash of the token, never the token itself. The raw token exists only in the email.
- Expose lookup through a `security definer` RPC that takes the token, and returns only what the invite page needs to render: organization name and role. Never the invite list, never other invitees' emails.
- Acceptance is a second RPC that, in one transaction, checks expiry, checks `accepted_at is null`, inserts the membership, and stamps `accepted_at`. Doing this client-side in two calls leaves a window where the invite can be redeemed twice.
- Decide explicitly whether the invite is bound to the email address it was sent to. If it is, compare against `auth.email()` inside the RPC. If it is not, say so in the product, because the link is then a bearer token.

## 6. Verify

This is the step that distinguishes a finished job from a plausible one.

Run the static audit in `references/AUDIT.md`. It checks, in SQL: public tables with RLS disabled, security definer functions without a pinned `search_path`, functions still executable by `anon` or `public`, UPDATE policies missing `with check`, policies that apply to the `public` role, and views created without `security_invoker`.

Then run the cross-tenant proof, also in `references/AUDIT.md`. Two organizations, two users, then impersonate each in a transaction and assert that every tenant table returns zero rows belonging to the other organization, and that an UPDATE attempting to move a row across the boundary is rejected. A fix without this test is not verified, it is assumed.

Finally, run the platform's own checks, which catch things the queries above do not:

```bash
supabase db lint --level warning
```

and the security advisor in the dashboard or through the Supabase MCP server.

## Failure modes worth recognizing quickly

| Symptom | Cause |
| --- | --- |
| `infinite recursion detected in policy for relation "memberships"` (42P17) | A policy on a table queries that same table directly instead of through a security definer function |
| Query is instant locally, times out in production | `auth.uid()` not wrapped in a subquery, or no index on the policy's `org_id` column, or a policy that joins to find the tenant |
| Server code sees all rows, client sees none | The server is using the service role key, which bypasses RLS entirely. It must do its own tenant check |
| A view returns rows the base table would deny | Views run as their owner unless created `with (security_invoker = on)` |
| Rows appear under the wrong organization after an edit | UPDATE policy has `using` but no `with check` |
| Works for a signed-in user, also works for the anon key | Policy has no `to authenticated`, or the table has RLS disabled entirely |

## Where this stops

This skill covers the policy layer. It does not cover the application-side invite emails, the org-switching UI, or the billing seat count that usually sits on top of `memberships`. Those are product decisions, and the policies above do not constrain them.
