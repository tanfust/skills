# This skill has moved

`supabase-auth-emails` now lives in the Tanfust skills pack at **[github.com/tanfust/skills](https://github.com/tanfust/skills)**, under `skills/supabase-auth-emails/`. The history of this repo was merged into that one, and this is where fixes land from now on. This repo stays up so existing links keep working, but it will not be updated.

The version in the pack is a rewrite: it covers the `token_hash` link flow that works when the email is opened on a different device, custom SMTP, pushing templates to the hosted project with `supabase config push`, a failure-modes table, and a verification section that reads the sent message back out of Mailpit.

## Install from the new home

Claude Code, as a plugin:

```
/plugin marketplace add tanfust/skills
/plugin install tanfust-skills@tanfust
```

Any agent, via the skills CLI (Claude Code, Cursor, Codex, Copilot, Windsurf, Gemini, Cline, opencode, Zed):

```bash
npx skills add tanfust/skills --skill supabase-auth-emails
```

Or the whole pack:

```bash
npx skills add tanfust/skills
```

If you installed this skill from this repo by copying the directory, replace it with the copy from the pack. The skill name is unchanged, so nothing else needs to move.

## License

MIT, same as the pack.
