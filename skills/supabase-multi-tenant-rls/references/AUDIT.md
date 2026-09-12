# Verification

Two parts. The static audit finds structural holes without knowing anything about the schema. The cross-tenant proof is the one that actually demonstrates isolation. Run both. Report findings as a list of concrete violations, not a summary.

- [Static audit](#static-audit)
- [Cross-tenant proof](#cross-tenant-proof)
- [Reporting](#reporting)

## Static audit

Run each query against the project database. Every one of them should return zero rows. Any row returned is a finding, and the query name is the finding's title.

### 1. Public tables with RLS disabled

Anything here is readable and writable through the Data API by anyone holding the anon key.

```sql
select c.relname as table_name
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public'
  and c.relkind = 'r'
  and not c.relrowsecurity
order by 1;
```

### 2. Tables with RLS enabled but no policies

Not a leak, the table denies everything. Usually means a migration landed half-finished and a feature is silently broken.

```sql
select c.relname as table_name
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public'
  and c.relkind = 'r'
  and c.relrowsecurity
  and not exists (
    select 1 from pg_policy p where p.polrelid = c.oid
  )
order by 1;
```

### 3. Security definer functions without a pinned search_path

The escalation path. Each of these can be made to read an attacker-controlled table while running as the function owner.

```sql
select p.proname as function_name, p.proconfig
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.prosecdef
  and (
    p.proconfig is null
    or not exists (
      select 1 from unnest(p.proconfig) cfg where cfg like 'search_path=%'
    )
  )
order by 1;
```

### 4. Security definer functions callable by anon

Postgres grants EXECUTE to PUBLIC on new functions. Each row here is an RLS bypass reachable without a session.

```sql
select p.proname as function_name
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.prosecdef
  and has_function_privilege('anon', p.oid, 'execute')
order by 1;
```

Expect deliberate exceptions here, such as an invite lookup RPC. Confirm each one is intentional rather than silencing the query.

### 5. UPDATE policies without a with_check clause

Lets a caller move a row across the tenant boundary by editing its `org_id`.

```sql
select tablename, policyname
from pg_policies
where schemaname = 'public'
  and cmd in ('UPDATE', 'ALL')
  and with_check is null
order by 1, 2;
```

### 6. Policies that apply to the public role

These run for `anon` as well as `authenticated`.

```sql
select tablename, policyname, roles
from pg_policies
where schemaname = 'public'
  and roles = '{public}'
order by 1, 2;
```

### 7. Views without security_invoker

A view without it runs as its owner and reads straight past RLS on its base tables.

```sql
select c.relname as view_name, c.reloptions
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public'
  and c.relkind in ('v', 'm')
  and (
    c.reloptions is null
    or not (
      'security_invoker=true' = any(c.reloptions)
      or 'security_invoker=on' = any(c.reloptions)
    )
  )
order by 1;
```

### 8. Tenant tables missing an index on org_id

Not a security finding, a latency one. Every policy that calls a helper with `org_id` will sequential-scan without it.

```sql
select c.relname as table_name
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
join pg_attribute a on a.attrelid = c.oid and a.attname = 'org_id' and a.attnum > 0
where n.nspname = 'public'
  and c.relkind = 'r'
  and not exists (
    select 1
    from pg_index i
    where i.indrelid = c.oid
      and a.attnum = any(i.indkey)
  )
order by 1;
```

### 9. Realtime publication members without RLS

```sql
select pt.tablename
from pg_publication_tables pt
join pg_class c on c.relname = pt.tablename
join pg_namespace n on n.oid = c.relnamespace and n.nspname = pt.schemaname
where pt.pubname = 'supabase_realtime'
  and not c.relrowsecurity
order by 1;
```

### 10. Platform checks

Run these too. They cover things the catalog queries cannot see.

```bash
supabase db lint --level warning
```

Plus the security advisor, through the dashboard or the Supabase MCP server's advisor tool.

## Cross-tenant proof

The static audit proves the shape is right. This proves the behaviour is.

Run it against a local `supabase start` database or a branch, never production. It creates and rolls back real rows.

### Setup

```sql
-- Two organizations, two users, one row of data each.
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'a@example.test'),
  ('22222222-2222-2222-2222-222222222222', 'b@example.test');

insert into public.organizations (id, name, slug) values
  ('aaaaaaaa-0000-0000-0000-000000000000', 'Org A', 'org-a'),
  ('bbbbbbbb-0000-0000-0000-000000000000', 'Org B', 'org-b');

insert into public.memberships (org_id, user_id, role) values
  ('aaaaaaaa-0000-0000-0000-000000000000', '11111111-1111-1111-1111-111111111111', 'owner'),
  ('bbbbbbbb-0000-0000-0000-000000000000', '22222222-2222-2222-2222-222222222222', 'owner');
```

Then insert one row per tenant table for each org, as the service role.

### Impersonation

`auth.uid()` reads the `request.jwt.claims` setting, so a session can be impersonated inside a transaction. Set the claims first, while still privileged, then drop to the `authenticated` role.

```sql
begin;

select set_config(
  'request.jwt.claims',
  json_build_object(
    'sub',  '11111111-1111-1111-1111-111111111111',
    'role', 'authenticated',
    'email','a@example.test'
  )::text,
  true                    -- local to this transaction
);
set local role authenticated;

-- confirm the impersonation took
select auth.uid();        -- expect 1111...

rollback;
```

### Assertions

Each of these runs inside the impersonated transaction. Wrap them so a failure raises rather than prints, otherwise a wrong result scrolls past unnoticed.

```sql
begin;
select set_config('request.jwt.claims',
  '{"sub":"11111111-1111-1111-1111-111111111111","role":"authenticated"}', true);
set local role authenticated;

do $$
declare
  leaked int;
begin
  -- 1. no rows from the other organization are visible
  select count(*) into leaked
  from public.documents
  where org_id = 'bbbbbbbb-0000-0000-0000-000000000000';
  if leaked <> 0 then
    raise exception 'LEAK: user A can read % rows from org B', leaked;
  end if;

  -- 2. the roster of the other organization is not visible
  select count(*) into leaked
  from public.memberships
  where org_id = 'bbbbbbbb-0000-0000-0000-000000000000';
  if leaked <> 0 then
    raise exception 'LEAK: user A can read org B membership';
  end if;
end $$;

rollback;
```

Then the write-side assertions, which are the ones a read-only test misses:

```sql
begin;
select set_config('request.jwt.claims',
  '{"sub":"11111111-1111-1111-1111-111111111111","role":"authenticated"}', true);
set local role authenticated;

do $$
begin
  -- 3. cannot insert into another organization
  begin
    insert into public.documents (org_id, title)
    values ('bbbbbbbb-0000-0000-0000-000000000000', 'planted');
    raise exception 'LEAK: user A inserted into org B';
  exception when insufficient_privilege then
    null;  -- expected
  end;

  -- 4. cannot move an owned row into another organization
  begin
    update public.documents
    set org_id = 'bbbbbbbb-0000-0000-0000-000000000000'
    where org_id = 'aaaaaaaa-0000-0000-0000-000000000000';
    if found then
      raise exception 'LEAK: user A moved a row into org B (missing with check)';
    end if;
  exception when insufficient_privilege then
    null;  -- expected
  end;

  -- 5. cannot escalate own role
  begin
    update public.memberships
    set role = 'owner'
    where user_id = '11111111-1111-1111-1111-111111111111';
    -- if the caller is already owner in the fixture, run this as a 'member' instead
  exception when insufficient_privilege then
    null;
  end;
end $$;

rollback;
```

Note on assertion 3 and 4: a denied write raises `insufficient_privilege` (SQLSTATE 42501) for an INSERT that fails `with check`, while an UPDATE denied by `using` silently affects zero rows instead of raising. Both outcomes need handling, which is why the block checks `found` as well as catching the exception. This asymmetry is the reason cross-tenant UPDATE bugs survive manual testing for so long.

Repeat the whole block with user B against org A. Isolation is not symmetric by construction, and asymmetric policies are common once per-role rules appear.

## Reporting

State results as a table of `finding / table / severity / fix`, ordered by severity, and lead with anything from static audit 1, 3, 4, 5 or any failed cross-tenant assertion. Those are live exposure. Everything else is hygiene.

If all queries return zero rows and all assertions pass, say so plainly and name what was checked, so the result is auditable later rather than a claim that it looked fine.
