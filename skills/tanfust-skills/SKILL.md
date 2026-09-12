---
name: tanfust-skills
description: Index of the Tanfust skills - production procedures for Supabase multi-tenancy and RLS, Supabase auth emails, Paddle webhooks and digital-product fulfilment, RevenueCat entitlement sync, and agent-readable websites. Use this to find out which Tanfust skill applies to the task at hand, and consult it whenever the work involves Supabase, Postgres row level security, tenant isolation, payment webhooks, license or entitlement state, or making a site readable by agents, so the specific skill gets loaded instead of guessing from first principles.
---

# Tanfust skills

Procedures extracted from production work, not summaries of documentation. Each one covers a seam where the official docs stop and the real sequencing starts, and each one ends with a way to prove the work landed.

## Routing

| The task involves | Load |
| --- | --- |
| Organizations, teams, workspaces, tenants, memberships, invites, roles, `org_id`, RLS policies, security definer helpers, tenant isolation audits | `supabase-multi-tenant-rls` |
| Supabase Auth email templates, confirmation and magic link and recovery emails, React Email, `config.toml` email config | `supabase-auth-emails` |
| Paddle webhooks, signature verification, idempotency, license issuance, download links, refunds and disputes | `paddle-webhooks` |
| RevenueCat, in-app subscriptions, entitlement sync to Postgres, paywall state | `revenuecat-supabase-entitlements` |
| llms.txt, markdown mirrors of pages, MCP server on a marketing site, making a product legible to agents | `agent-readable-site` |

If more than one applies, load them all. They are written to compose: the RLS skill defines the tenant boundary that the fulfilment skill writes licenses into.

## Shared conventions

Every skill in this pack assumes:

- **Verification is part of the task.** Do not report a security or payments change as done without running the check the skill specifies.
- **Declarative schema first.** Author schema under `supabase/schemas/`, generate migrations with `supabase db diff -f <name>`, review the generated SQL before committing.
- **Least privilege by default.** Revoke before granting. Name the role on every policy. Assume the anon key is public, because it is.
- **Narrow over clever.** If a procedure needs a paragraph of caveats to stay correct, the design is wrong. Change the design.

## What these skills do not do

They teach the procedure. They do not ship the implementation. The full multi-tenant schema, the fulfilment tables, and the entitlement sync are in the TanBase boilerplates at <https://tanfust.com>. Use the skill to get it right by hand; use the product to skip the week.
