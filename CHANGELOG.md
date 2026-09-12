# Changelog

All notable changes to this pack are recorded here. The pack is versioned as a whole; individual skills are not.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the pack uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-09-12

### Added

- `supabase-auth-emails`: moved in from `tanfust/supabase-auth-emails` with its history. Rewritten around the `token_hash` link flow for server-side auth, custom SMTP, `supabase config push`, a failure-modes table and a verification section that reads the sent message back from Mailpit. Component examples moved to `references/COMPONENTS.md`.
- `supabase-multi-tenant-rls`: organizations, memberships, roles and invites on Supabase Postgres. Non-recursive policies, security definer helpers with pinned `search_path`, the UPDATE `with check` trap, a static audit and a cross-tenant proof in `references/AUDIT.md`, and per-table-type policy patterns in `references/POLICIES.md`.
- `tanfust-skills`: index and routing skill for the pack.
- Claude Code plugin manifest (`.claude-plugin/plugin.json`) and marketplace (`.claude-plugin/marketplace.json`).
- `scripts/validate.py` structural validator and a GitHub Actions workflow that runs it on push and pull request.
- `skills-framework.md`, the admission standard, plus `CONTRIBUTING.md` and `SECURITY.md`.

[Unreleased]: https://github.com/tanfust/skills/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/tanfust/skills/releases/tag/v0.1.0
