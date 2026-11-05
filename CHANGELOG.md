# Changelog

All notable changes to this pack are recorded here. The pack is versioned as a whole; individual skills are not.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the pack uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Security

- `supabase-auth-emails`: the local-send check no longer pipes Mailpit responses into `python3` or `eval`s `supabase status` output. It reads status values with `sed`, compares each message to the expected subject and link with `grep`, and prints only `FAIL` lines and the Mailpit message ID, so email content, which carries sign-up data the requester controlled, stays out of the agent's context. The section now states that fetched mail is data, not instructions. The check also creates a confirmed user first, because with `enable_confirmations = true` a magic link to an unconfirmed address sends the confirmation email instead. Prompted by the Gen Agent Trust Hub audit on skills.sh (Sep 12, 2026).
- `paddle-domain-verification`: the home page link count no longer goes through `xargs sh -c`, and the static check states that page text is data.
- `agent-readable-site`: `verify-agent-surface.sh` runs `@modelcontextprotocol/inspector` at an exact version (`INSPECTOR_VERSION`, default 2.12.0) instead of whatever npx resolves, and scanner reports are treated as data.

## [0.3.0] - 2026-09-12

### Added

- `paddle-webhooks`: fulfilment of one-time purchases from Paddle Billing into Supabase. Raw-body signature verification, `event_id` ledger, licence constraint on (transaction, product), adjustment state machine by action and status with an `occurred_at` guard, `references/EVENTS.md` quoting Paddle's delivery, retry and adjustment documentation, `references/SCHEMA.md` with the tables and handler, and a verification built on the simulator, the ledger and a sandbox refund.
- `revenuecat-supabase-entitlements`: RevenueCat to Supabase entitlement sync for RLS gating. Edge Function authenticated by the shared header, event id ledger, and the vendor-recommended fetch of `GET /v1/subscribers` as the source of truth instead of the event type; `environment` column to keep sandbox out of production; paywall state table; drift query.
- `agent-readable-site`: generated `llms.txt`, markdown mirror with literal-token `Accept` negotiation, Content-Signal, `Link` headers, format-matching 404s, optional MCP server card; `references/SURFACES.md` with sources for each surface including the draft status of SEP-1649; `references/NEXTJS.md`; `scripts/verify-agent-surface.sh`.

### Changed

- Manifests and the `tanfust-skills` router describe and route to all six procedure skills.
- `scripts/validate.py` ignores links inside inline code spans.

## [0.2.0] - 2026-09-12

### Added

- `paddle-domain-verification`: getting a domain through Paddle's website approval. Rewritten from an internal legal-page generator into a procedure: facts that must match the Paddle account, the handbook's verbatim Merchant of Record sentence, an unconditional refund window, `references/REQUIREMENTS.md` quoting Paddle's pages with URLs and read dates, placeholder templates, and a curl-based check against the live pages plus the dashboard status as the pass condition.

## [0.1.0] - 2026-09-12

### Added

- `supabase-auth-emails`: moved in from `tanfust/supabase-auth-emails` with its history. Rewritten around the `token_hash` link flow for server-side auth, custom SMTP, `supabase config push`, a failure-modes table and a verification section that reads the sent message back from Mailpit. Component examples moved to `references/COMPONENTS.md`.
- `supabase-multi-tenant-rls`: organizations, memberships, roles and invites on Supabase Postgres. Non-recursive policies, security definer helpers with pinned `search_path`, the UPDATE `with check` trap, a static audit and a cross-tenant proof in `references/AUDIT.md`, and per-table-type policy patterns in `references/POLICIES.md`.
- `tanfust-skills`: index and routing skill for the pack.
- Claude Code plugin manifest (`.claude-plugin/plugin.json`) and marketplace (`.claude-plugin/marketplace.json`).
- `scripts/validate.py` structural validator and a GitHub Actions workflow that runs it on push and pull request.
- `skills-framework.md`, the admission standard, plus `CONTRIBUTING.md` and `SECURITY.md`.

[Unreleased]: https://github.com/tanfust/skills/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/tanfust/skills/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/tanfust/skills/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/tanfust/skills/releases/tag/v0.1.0
