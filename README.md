# Tanfust Skills

Agent skills for the parts of shipping a product where the documentation stops and the sequencing starts.

Each skill here is a procedure extracted from production work, not a summary of a vendor's docs. Every one of them ends with a way to prove the change landed, because the failures in this territory are silent: a wrong RLS policy returns rows instead of an error, and a wrong webhook handler charges someone twice.

## Install

**Claude Code, as a plugin**

```
/plugin marketplace add tanfust/skills
/plugin install tanfust-skills@tanfust
```

**Any agent, via the skills CLI**

```bash
npx skills add tanfust/skills
npx skills add tanfust/skills --skill supabase-multi-tenant-rls
```

Works with Claude Code, Cursor, Codex, Copilot, Windsurf, Gemini, Cline, opencode, Zed and the rest.

**By hand**

Copy the skill directory into `~/.claude/skills/` or your agent's equivalent.

## Skills

| Skill | What it covers |
| --- | --- |
| [`supabase-multi-tenant-rls`](skills/supabase-multi-tenant-rls) | Organizations, memberships, roles and invites. Non-recursive policies, security definer helpers that cannot be shadowed, the UPDATE `with check` trap, and a cross-tenant proof that either passes or names the leak. |
| [`tanfust-skills`](skills/tanfust-skills) | Index and routing for the pack. |

Shipping next, in order:

- `supabase-auth-emails` (currently at [tanfust/supabase-auth-emails](https://github.com/tanfust/supabase-auth-emails), moving here)
- `paddle-webhooks` — signature verification, idempotency ledger, out-of-order delivery, license issuance, refund and dispute revocation
- `revenuecat-supabase-entitlements` — webhook to entitlement sync, the states a paywall actually has to handle
- `agent-readable-site` — llms.txt, markdown mirrors, an MCP server on a marketing site, Content-Signal

## What these skills are not

They teach the procedure. They do not ship the implementation.

The full multi-tenant schema, the fulfilment tables, and the entitlement sync are in the TanBase boilerplates at [tanfust.com](https://tanfust.com). Use a skill to get it right by hand. Use the product to skip the week.

## Contributing

Issues and PRs welcome, with one rule that decides everything: a skill gets merged if it is a procedure someone has run in production at least three times, and it defines how to verify the result. Skills that restate documentation get closed, politely.

## License

MIT. See [LICENSE](LICENSE).
