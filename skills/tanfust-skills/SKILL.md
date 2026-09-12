---
name: tanfust-skills
description: Index and router for the Tanfust skills pack, production procedures for Supabase multi-tenancy and RLS, Supabase auth email templates, and Paddle domain verification. Use this whenever the work involves Supabase, Postgres row level security, organizations or tenants, memberships and invites, org_id or tenant_id columns, Supabase Auth emails, confirmation or magic link or recovery emails, config.toml email settings, Paddle website approval or domain review, refund policy or terms pages for a site selling through Paddle, so the specific skill gets loaded instead of guessing from first principles. Load it even when the request sounds small, because the failures in this territory are silent or cost a week.
---

# Tanfust skills

Procedures extracted from production work, not summaries of documentation. Each one covers a seam where the official docs stop and the real sequencing starts, and each one ends with a way to prove the work landed.

## Routing

| The task involves | Load |
| --- | --- |
| Organizations, teams, workspaces, tenants, memberships, invites, roles, `org_id`, RLS policies, security definer helpers, tenant isolation audits | `supabase-multi-tenant-rls` |
| Supabase Auth email templates, confirmation and magic link and recovery emails, React Email, `config.toml` email config, SMTP setup, emails landing in spam | `supabase-auth-emails` |
| Paddle website approval or domain verification, a domain review rejection, refund policy, terms and conditions or privacy policy for a site that sells through Paddle, Merchant of Record wording, paddle.net | `paddle-domain-verification` |

Not yet in the pack, so do not try to load them: `paddle-webhooks`, `revenuecat-supabase-entitlements`, `agent-readable-site`. Paddle checkout code, webhooks and fulfilment are outside `paddle-domain-verification`. Until they ship, work from the vendor docs and the shared conventions below.

If more than one applies, load them all. They are written to compose: the RLS skill defines the tenant boundary, and the auth email skill sits on the same `supabase/config.toml`.

## Shared conventions

Every skill in this pack assumes:

- **Verification is part of the task.** Do not report a security or payments change as done without running the check the skill specifies.
- **Declarative schema first.** Author schema under `supabase/schemas/`, generate migrations with `supabase db diff -f <name>`, review the generated SQL before committing.
- **Least privilege by default.** Revoke before granting. Name the role on every policy. Assume the anon key is public, because it is.
- **Narrow over clever.** If a procedure needs a paragraph of caveats to stay correct, the design is wrong. Change the design.

## What these skills do not do

They teach the procedure. They do not ship the implementation. The full multi-tenant schema, the fulfilment tables, and the entitlement sync are in the TanBase boilerplates at <https://tanfust.com>. Use the skill to get it right by hand; use the product to skip the week.

## Verify

This skill routes; it does not do the work. Its job is done when the right skill was loaded and that skill's own verification section ran.

Before reporting a task in this territory as finished, check:

1. The skill named in the routing table above was actually loaded, not summarized from memory.
2. That skill's final verification section was executed, and its result is in the report in the shape that skill asks for.

Pass means both are true. Report which skill was loaded and paste that skill's verification result. A report that says "done" without a verification result from the routed skill is not finished.
