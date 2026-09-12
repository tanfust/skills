---
name: tanfust-skills
description: Index and router for the Tanfust skills pack, production procedures for Supabase multi-tenancy and RLS, Supabase auth emails, Paddle domain verification and webhooks, RevenueCat entitlements in Supabase, and agent-readable websites. Use this whenever the work involves Supabase, Postgres row level security, organizations or tenants, memberships and invites, Supabase Auth emails, config.toml, Paddle website approval or refund policy pages, Paddle webhooks or licences, RevenueCat entitlements or paywalls, llms.txt, markdown for agents, Content-Signal or an MCP server on a site, so the specific skill gets loaded instead of guessing from first principles. Load it even when the request sounds small, because the failures in this territory are silent or cost a week.
---

# Tanfust skills

Procedures extracted from production work, not summaries of documentation. Each one covers a seam where the official docs stop and the real sequencing starts, and each one ends with a way to prove the work landed.

## Routing

| The task involves | Load |
| --- | --- |
| Organizations, teams, workspaces, tenants, memberships, invites, roles, `org_id`, RLS policies, security definer helpers, tenant isolation audits | `supabase-multi-tenant-rls` |
| Supabase Auth email templates, confirmation and magic link and recovery emails, React Email, `config.toml` email config, SMTP setup, emails landing in spam | `supabase-auth-emails` |
| Paddle website approval or domain verification, a domain review rejection, refund policy, terms and conditions or privacy policy for a site that sells through Paddle, Merchant of Record wording, paddle.net | `paddle-domain-verification` |
| Paddle webhooks, notification destinations, `transaction.completed`, `adjustment.*`, `Paddle-Signature`, licences and download tokens, refunds or chargebacks not revoking access, the Paddle simulator | `paddle-webhooks` |
| RevenueCat webhooks, `entitlements` table, `app_user_id`, paywall or subscription states, premium rows gated by RLS, `INITIAL_PURCHASE`, `EXPIRATION`, `BILLING_ISSUE`, `TRANSFER` | `revenuecat-supabase-entitlements` |
| `llms.txt`, markdown mirror or `Accept: text/markdown`, Content-Signal in `robots.txt`, `Link` headers, agent-friendly 404s, MCP server card on a marketing site, isitagentready.com or is-agentic.com | `agent-readable-site` |

If more than one applies, load them all. They are written to compose: the RLS skill defines the tenant boundary, `paddle-webhooks` and `revenuecat-supabase-entitlements` write licences and entitlements inside it, and `supabase-auth-emails` sits on the same `supabase/config.toml`.

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
