---
name: supabase-auth-emails
description: Replace Supabase Auth's default emails (confirmation, magic link, recovery, invite, email change) with branded React Email templates, wire them through supabase/config.toml, push them to the hosted project with supabase config push, and prove they render and deliver. Use this whenever the work touches Supabase auth emails or templates, [auth.email.template.*] or content_path in config.toml, {{ .ConfirmationURL }} or {{ .TokenHash }}, React Email rendered to static HTML for Supabase, custom SMTP via [auth.email.smtp] or Resend, Mailpit or Inbucket on localhost:54324, magic links that fail on another device, "Email link is invalid or has expired", "both auth code and code verifier should be non-empty", or auth emails that never arrive, land in spam, or still look like the Supabase default in production. Reach for it even for "just restyle the confirmation email", because the failures here are silent and reach customers. Not for product emails sent from application code, and not for the auth routes themselves.
license: MIT
---

# Supabase Auth emails with React Email

Two things go wrong with auth emails, and neither throws. The template looks right in the local mail catcher and production keeps sending the Supabase default, because `config.toml` is local configuration and nobody pushed it. Or the email arrives, the button works on the laptop that requested it, and fails for every customer who opens it on their phone, because the link depends on a cookie that only exists in the first browser. So the work is not finished when the template renders. It is finished when a link from a real send, opened in a browser that did not request it, produces a signed-in session, locally and on the hosted project.

This skill covers the five action emails Supabase lets you template: `confirmation`, `magic_link`, `recovery`, `invite`, `email_change`. React Email is the authoring tool; Supabase only ever sees static HTML with Go template variables in it.

## Order of work

1. Decide the link flow before writing any template
2. Set up custom SMTP, because the default sender does not reach customers
3. Write the templates against a shared layout
4. Build to static HTML with the Go variables passed through as props
5. Wire `config.toml` and restart the local stack
6. Push to the hosted project
7. Verify: build, send, open on another device, check production

## 1. Decide the link flow

`{{ .ConfirmationURL }}` points at Supabase's `/auth/v1/verify` endpoint, which verifies the token and redirects to your site. With the implicit flow that is all you need. With server-side auth (`@supabase/ssr`, Next.js App Router, SvelteKit, Remix) the client starts a PKCE exchange and stores a code verifier in a cookie in the browser that requested the email. If the user opens the link anywhere else, the exchange fails with `both auth code and code verifier should be non-empty`. That is most users: they sign up on a laptop and tap the link on their phone.

The fix is to build the link yourself from `{{ .TokenHash }}` and verify it in a server route that does not need the cookie:

```
{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=email&next={{ .RedirectTo }}
```

- `type` is what your route passes to `supabase.auth.verifyOtp({ type, token_hash })`. `email` covers confirmation and magic link. Use `recovery`, `invite` and `email_change` for the others.
- `next={{ .RedirectTo }}`: Supabase substitutes `RedirectTo` with the `emailRedirectTo` the client passed to `signInWithOtp` or `signUp`, so the user's intended destination survives the round trip. Your route must validate `next` as same-origin before redirecting, or you have shipped an open redirect.
- `{{ .SiteURL }}` is the project's Site URL, not the request origin. Locally that is whatever `site_url` says in `config.toml`; in production it is the value in Auth settings. If the two disagree with where the app actually runs, every link points at the wrong host.

Decide this per template and write it down in the build script, which is the only place the URL is assembled. Mixing flows across templates is how one email in five breaks.

## 2. Set up custom SMTP

Supabase's built-in sender is for development. On hosted projects it only delivers to addresses belonging to project team members and is tightly rate limited. A new customer signing up gets nothing, the API returns success, and the first report is a support ticket days later. Configure `[auth.email.smtp]` before shipping any template, and use a subdomain for the sender so a deliverability problem cannot damage the root domain's reputation:

```toml
[auth.email.smtp]
enabled = true
host = "smtp.resend.com"
port = 465
user = "resend"
pass = "env(RESEND_API_KEY)"
admin_email = "env(RESEND_FROM_EMAIL)"
```

`env(...)` reads from the CLI's environment, so the key never lands in the repo. On the hosted side the same settings live under Auth, SMTP, and are also covered by `supabase config push`. Set SPF and DKIM on the sending subdomain at the provider before the first real send; without them the first thing your branded template does is land in spam.

## 3. Write the templates

Author under `emails/` with a shared layout in `emails/_components/`. The underscore prefix keeps shared parts out of the React Email preview list. Typed props, one component per Supabase type, `PreviewProps` on each so `email dev` renders something useful.

Email clients dictate the styling rules, and violating them does not error, it just renders wrong somewhere you did not test: no flexbox or grid, no `rem`, no media queries, no SVG or WebP, `box-border` or an explicit `boxSizing` on buttons so Outlook does not overflow the padding, `border-solid` or an explicit `borderStyle` on every `Hr` because clients do not inherit border style and an unstyled rule renders as nothing. Always include the raw URL as text under the button, because some clients strip button markup.

Read the project's existing theme before choosing colours: `globals.css` custom properties, `tailwind.config.*`, a `config/site.ts` with the app name and support address. A template that matches the app is the whole point of doing this instead of editing HTML in the dashboard.

Full layout and template components are in `references/COMPONENTS.md`. Read it when writing a template from scratch; the body here assumes the shape.

## 4. Build to static HTML

Supabase needs files on disk. A build script renders each component with the Go template strings passed in as ordinary prop values, so `{{ .ConfirmationURL }}` survives into the HTML as literal text:

```typescript
// scripts/build-email-templates.ts
import { render } from "react-email";          // "@react-email/components" on v3 and earlier
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import MagicLinkEmail from "../emails/magic-link";
import ConfirmSignUpEmail from "../emails/confirm-sign-up";

const SB = {
  confirmationUrl: "{{ .ConfirmationURL }}",
  email: "{{ .Email }}",
  newEmail: "{{ .NewEmail }}",
};

const templates = [
  { name: "magic-link", element: MagicLinkEmail({
      confirmationUrl: "{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=email&next={{ .RedirectTo }}",
      email: SB.email }) },
  { name: "confirm-sign-up", element: ConfirmSignUpEmail({ confirmationUrl: SB.confirmationUrl, email: SB.email }) },
  // recovery, invite, email_change follow the same shape
];

const outDir = join(import.meta.dirname, "..", "supabase", "templates");
mkdirSync(outDir, { recursive: true });
for (const { name, element } of templates) {
  writeFileSync(join(outDir, `${name}.html`), await render(element), "utf-8");
}
```

Add `"email:build-templates": "tsx scripts/build-email-templates.ts"` to `package.json` and commit the generated HTML. The CLI reads the files, not the components, so an uncommitted `supabase/templates/` means CI and teammates run with the defaults.

Do not put the Go variables in `PreviewProps`. Those are for the preview server and should hold realistic values so a designer can judge the layout.

## 5. Wire config.toml and restart

```toml
[auth.email.template.magic_link]
subject = "Your sign-in link"
content_path = "./supabase/templates/magic-link.html"

[auth.email.template.confirmation]
subject = "Confirm your account"
content_path = "./supabase/templates/confirm-sign-up.html"

[auth.email.template.recovery]
subject = "Reset your password"
content_path = "./supabase/templates/reset-password.html"

[auth.email.template.invite]
subject = "You have been invited"
content_path = "./supabase/templates/invite-user.html"

[auth.email.template.email_change]
subject = "Confirm your new email"
content_path = "./supabase/templates/change-email.html"
```

Paths resolve from the project root, where you run the CLI. There is no `reauthentication` key; that email cannot be templated through the CLI. The local stack reads `config.toml` at start, so after any change run `supabase stop && supabase start`. Editing the HTML alone changes nothing until the restart either, which is the most common reason a fix "did not work".

Check `[auth.email]` while you are there: `enable_confirmations` decides whether the confirmation email is sent at all, and `max_frequency` is the minimum gap between two emails to the same address. A `max_frequency` of `1m` in production makes "resend the link" fail silently for a minute.

## 6. Push to the hosted project

`config.toml` configures the local stack and nothing else. The hosted project keeps its own copy of every template and subject. After `supabase link`, push:

```bash
supabase config push
```

The CLI prints a diff of what will change on the remote, including the template bodies. Read it. Then confirm in the dashboard under Authentication, Emails, that each template shows your HTML. Do this on every template change, or add it to the deploy pipeline. A team that edits templates locally and forgets this step ships the default Supabase email to customers for months with no error anywhere.

## Failure modes worth recognizing quickly

| Symptom | Cause |
| --- | --- |
| Link works on the machine that requested it, fails elsewhere with `both auth code and code verifier should be non-empty` | Server-side auth using `{{ .ConfirmationURL }}`. Switch that template to the `token_hash` flow in step 1 |
| `Email link is invalid or has expired` (`error_code=otp_expired`) on first click | The link was consumed before the user clicked it, usually by a corporate mail scanner that prefetches URLs. The token is single-use. Move verification behind a page with a button or a POST so a GET cannot consume it |
| Email arrives locally, production sends the Supabase default | `config.toml` was never pushed. Step 6 |
| Sign-up succeeds, no email arrives in production, team addresses do receive it | Built-in sender restricted to team members. Step 2 |
| Email arrives with `{{ .ConfirmationURL }}` printed in it | Template loaded from a path with no such file, so Supabase fell back to raw text, or the build encoded the braces. Check the `content_path` and grep the HTML |
| Button links to `localhost` in production | `site_url` in the hosted Auth settings is wrong, or the template hardcodes a host instead of `{{ .SiteURL }}` |
| Template changes have no effect locally | Local stack not restarted after the edit |
| `Hr` renders as nothing, button padding overflows in Outlook | Missing `border-solid` on `Hr`, missing `box-border` on `Button` |
| Second magic link request returns a rate limit error | `max_frequency` in `[auth.email]`, or the hosted email rate limit |

## 7. Verify

Four checks. The first two are mechanical, the third is the one that proves the thing works, the fourth is the one people skip.

**Build and paths.** Run the build, then confirm every `content_path` in `config.toml` exists and every generated file still carries a link variable:

```bash
pnpm email:build-templates
grep -oE 'content_path = "[^"]+"' supabase/config.toml | cut -d'"' -f2 | while read -r f; do [ -f "$f" ] || echo "MISSING $f"; done
grep -L -e '{{ .ConfirmationURL }}' -e '{{ .TokenHash }}' supabase/templates/*.html
grep -l -e '%7B%7B' -e '&#123;' supabase/templates/*.html
```

Pass: the three greps print nothing. Any filename printed is a finding.

**Local send.** Restart the stack, trigger a real flow through the Auth API rather than the UI, and read the message back from Mailpit's API (the CLI's mail catcher on port 54324; older CLIs ship Inbucket at the same port with a different API, in which case open it in the browser instead):

```bash
supabase stop && supabase start
eval "$(supabase status -o env)"
curl -s -X POST "$API_URL/auth/v1/magiclink" -H "apikey: $ANON_KEY" -H "Content-Type: application/json" \
  -d '{"email":"a@example.test"}'
ID=$(curl -s http://127.0.0.1:54324/api/v1/messages | python3 -c 'import sys,json; print(json.load(sys.stdin)["messages"][0]["ID"])')
curl -s "http://127.0.0.1:54324/api/v1/message/$ID" | python3 -c 'import sys,json; m=json.load(sys.stdin); print(m["Subject"]); print("{{" in m["HTML"], "token_hash=" in m["HTML"] or "/auth/v1/verify" in m["HTML"])'
```

Pass: the subject equals the one in `config.toml`, the first boolean is `False` (no unrendered Go syntax), the second is `True` (a real link). Repeat for `signup` and `recover` endpoints so all templates with a config entry have been sent at least once.

**Cross-device open.** Copy the link out of the Mailpit message and open it in a private window, which has none of the requesting browser's cookies. Pass: the app lands signed in at the `next` destination. A redirect to your error page is a failure of step 1, whatever the local preview looked like.

**Production.** After `supabase config push`, request a magic link against the hosted project from a non-team address you control, open it on a phone, and read the headers of the received message. Pass: signed-in session, `Authentication-Results` shows `spf=pass` and `dkim=pass`, and the dashboard's template page shows your HTML for all five types.

Report as a table of `check / template / result / evidence`, one row per template per check, with the Mailpit message ID or the production message's `Message-ID` as evidence. If everything passes, say so and list the five subjects observed, so the next person can tell a verified run from a claim.

## Where this stops

This skill covers the templates, the build, the CLI configuration and delivery. It does not cover the `/auth/confirm` route beyond what the link needs from it, the sign-in UI, or product emails sent from application code through Resend or similar; those use the same layout components but are rendered at send time, not built to static files. Notification emails (`[auth.email.notification.*]`, password changed, MFA enrolled and so on) are listed in `references/TEMPLATES.md` for completeness but have not been through this procedure in production, so treat that section as reference, not as verified.
