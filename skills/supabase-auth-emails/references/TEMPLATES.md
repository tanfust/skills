# Supabase Email Templates Reference

## Table of Contents

1. [Auth Templates (Action Required)](#auth-templates)
2. [Notification Templates (Informational)](#notification-templates)
3. [Complete Go Template Variables](#complete-go-template-variables)
4. [token_hash flow for server-side auth](#token_hash-flow-for-server-side-auth)


## Auth Templates

These templates contain a CTA (button or link) that the user must act on. Configured via `[auth.email.template.<type>]` in config.toml.

### 1. confirmation (Confirm Sign Up)

- **Purpose**: Sent after a user signs up to verify their email
- **CTA**: Button linking to `{{ .ConfirmationURL }}`
- **Variables**: `{{ .ConfirmationURL }}`, `{{ .Email }}`, `{{ .SiteURL }}`, `{{ .TokenHash }}`, `{{ .RedirectTo }}`
- **Subject example**: "Confirm your email"

### 2. invite (Invite User)

- **Purpose**: Sent when an admin invites a new user
- **CTA**: Button linking to `{{ .ConfirmationURL }}`
- **Variables**: `{{ .ConfirmationURL }}`, `{{ .Email }}`, `{{ .SiteURL }}`, `{{ .TokenHash }}`, `{{ .RedirectTo }}`
- **Subject example**: "You've been invited"

### 3. magic_link (Magic Link)

- **Purpose**: Passwordless sign-in link
- **CTA**: Button linking to `{{ .ConfirmationURL }}`
- **Variables**: `{{ .ConfirmationURL }}`, `{{ .Email }}`, `{{ .SiteURL }}`, `{{ .TokenHash }}`, `{{ .RedirectTo }}`
- **Subject example**: "Your sign-in link"

### 4. email_change (Change Email Address)

- **Purpose**: Verify new email address after changing it
- **CTA**: Button linking to `{{ .ConfirmationURL }}`
- **Variables**: `{{ .ConfirmationURL }}`, `{{ .Email }}`, `{{ .NewEmail }}`, `{{ .SiteURL }}`, `{{ .TokenHash }}`, `{{ .RedirectTo }}`
- **Subject example**: "Confirm email change"

### 5. recovery (Reset Password)

- **Purpose**: Password reset link
- **CTA**: Button linking to `{{ .ConfirmationURL }}`
- **Variables**: `{{ .ConfirmationURL }}`, `{{ .Email }}`, `{{ .SiteURL }}`, `{{ .TokenHash }}`, `{{ .RedirectTo }}`
- **Subject example**: "Reset your password"

### Reauthentication (not configurable via config.toml)

Supabase sends a reauthentication OTP email internally when a user attempts a sensitive action. There is no `[auth.email.template.reauthentication]` key in config.toml, this email cannot be customized through the template system. You can still create a React Email component for it for preview/documentation purposes.

- **CTA**: Displays OTP code `{{ .Token }}`, no `{{ .ConfirmationURL }}` available
- **Variables**: `{{ .Token }}`, `{{ .SiteURL }}`, `{{ .Email }}`, `{{ .Data }}`


## Notification Templates

Informational security alerts with no action link. Configured via `[auth.email.notification.<type>]` in config.toml, each with `enabled = true`, `subject` and `content_path` using the same `./supabase/templates/` convention as the action templates.

Reference only. These have not been through the SKILL.md procedure in production, so the variables below come from the Supabase CLI configuration reference rather than from a verified send. Run the full verification section against any of them before trusting it.

### 6. password_changed

- **Variables**: `{{ .Email }}`, `{{ .Data }}`
- **Subject example**: "Your password has been changed"

### 7. email_changed

- **Variables**: `{{ .Email }}`, `{{ .OldEmail }}`, `{{ .Data }}`
- **Subject example**: "Your email address has been changed"

### 8. phone_changed

- **Variables**: `{{ .Email }}`, `{{ .Phone }}`, `{{ .OldPhone }}`, `{{ .Data }}`
- **Subject example**: "Your phone number has been changed"

### 9. identity_linked

- **Variables**: `{{ .Email }}`, `{{ .Provider }}`, `{{ .Data }}`
- **Subject example**: "A new identity has been linked"

### 10. identity_unlinked

- **Variables**: `{{ .Email }}`, `{{ .Provider }}`, `{{ .Data }}`
- **Subject example**: "An identity has been unlinked"

### 11. mfa_factor_enrolled

- **Variables**: `{{ .Email }}`, `{{ .FactorType }}`, `{{ .Data }}`
- **Subject example**: "A new MFA method has been added"

### 12. mfa_factor_unenrolled

- **Variables**: `{{ .Email }}`, `{{ .FactorType }}`, `{{ .Data }}`
- **Subject example**: "An MFA method has been removed"


## Complete Go Template Variables

All variables available in Supabase email templates:

| Variable | Type | Description | Available In |
| --- | --- | --- | --- |
| `{{ .ConfirmationURL }}` | URL | Full confirmation/action URL | confirmation, invite, magic_link, email_change, recovery |
| `{{ .Token }}` | String | 6-digit OTP code | reauthentication (internal only) |
| `{{ .TokenHash }}` | String | Token hash for PKCE flows | confirmation, invite, magic_link, email_change, recovery |
| `{{ .RedirectTo }}` | URL | Post-action redirect URL | confirmation, invite, magic_link, email_change, recovery |
| `{{ .SiteURL }}` | URL | Application base URL | All templates |
| `{{ .Email }}` | String | User's email address | All templates |
| `{{ .NewEmail }}` | String | New email after change | email_change |
| `{{ .OldEmail }}` | String | Previous email address | email_changed notification |
| `{{ .Phone }}` | String | New phone number | phone_changed notification |
| `{{ .OldPhone }}` | String | Previous phone number | phone_changed notification |
| `{{ .Provider }}` | String | Identity provider name (e.g., "google", "github") | identity_linked, identity_unlinked notifications |
| `{{ .FactorType }}` | String | MFA factor type (e.g., "totp") | mfa_factor_enrolled, mfa_factor_unenrolled notifications |
| `{{ .Data }}` | Object | Custom user metadata | All templates |


## token_hash flow for server-side auth

With `@supabase/ssr` (Next.js App Router, SvelteKit, Remix) do not use `{{ .ConfirmationURL }}`; see step 1 of SKILL.md for why it breaks when the link is opened in a browser other than the one that requested it. Build the link from `{{ .TokenHash }}` and verify it in a server route:

```
{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=<type>&next={{ .RedirectTo }}
```

`type` is the `EmailOtpType` your route passes to `supabase.auth.verifyOtp({ type, token_hash })`:

| Template | `type` |
| --- | --- |
| confirmation | `email` (`signup` also accepted) |
| magic_link | `email` (`magiclink` also accepted) |
| recovery | `recovery` |
| invite | `invite` |
| email_change | `email_change` |

`next={{ .RedirectTo }}` carries the `emailRedirectTo` the client passed to `signInWithOtp` or `signUp`. The route must check that `next` is same-origin before redirecting to it.

Example button in a template. The URL is assembled in the build script and arrives as the `confirmationUrl` prop; the component does not know which flow it is in:

```tsx
<Button href={confirmationUrl} className="box-border bg-gray-900 text-white px-6 py-3 text-sm font-medium no-underline">
  Confirm email
</Button>
```

Use `{{ .ConfirmationURL }}` only when Supabase handles the redirect directly (implicit flow, no server-side session exchange).
