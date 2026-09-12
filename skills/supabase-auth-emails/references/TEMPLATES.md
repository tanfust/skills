# Supabase Email Templates Reference

## Table of Contents

1. [Auth Templates (Action Required)](#auth-templates)
2. [Notification Templates (Informational)](#notification-templates)
3. [Complete Go Template Variables](#complete-go-template-variables)
4. [PKCE Flow (Server-Side Auth)](#pkce-flow)

---

## Auth Templates

These templates contain a CTA (button or link) that the user must act on. Configured via `[auth.email.template.<type>]` in config.toml.

### 1. confirmation — Confirm Sign Up

- **Purpose**: Sent after a user signs up to verify their email
- **CTA**: Button linking to `{{ .ConfirmationURL }}`
- **Variables**: `{{ .ConfirmationURL }}`, `{{ .Email }}`, `{{ .SiteURL }}`, `{{ .TokenHash }}`, `{{ .RedirectTo }}`
- **Subject example**: "Confirm your email"

### 2. invite — Invite User

- **Purpose**: Sent when an admin invites a new user
- **CTA**: Button linking to `{{ .ConfirmationURL }}`
- **Variables**: `{{ .ConfirmationURL }}`, `{{ .Email }}`, `{{ .SiteURL }}`, `{{ .TokenHash }}`, `{{ .RedirectTo }}`
- **Subject example**: "You've been invited"

### 3. magic_link — Magic Link

- **Purpose**: Passwordless sign-in link
- **CTA**: Button linking to `{{ .ConfirmationURL }}`
- **Variables**: `{{ .ConfirmationURL }}`, `{{ .Email }}`, `{{ .SiteURL }}`, `{{ .TokenHash }}`, `{{ .RedirectTo }}`
- **Subject example**: "Your sign-in link"

### 4. email_change — Change Email Address

- **Purpose**: Verify new email address after changing it
- **CTA**: Button linking to `{{ .ConfirmationURL }}`
- **Variables**: `{{ .ConfirmationURL }}`, `{{ .Email }}`, `{{ .NewEmail }}`, `{{ .SiteURL }}`, `{{ .TokenHash }}`, `{{ .RedirectTo }}`
- **Subject example**: "Confirm email change"

### 5. recovery — Reset Password

- **Purpose**: Password reset link
- **CTA**: Button linking to `{{ .ConfirmationURL }}`
- **Variables**: `{{ .ConfirmationURL }}`, `{{ .Email }}`, `{{ .SiteURL }}`, `{{ .TokenHash }}`, `{{ .RedirectTo }}`
- **Subject example**: "Reset your password"

### Reauthentication (not configurable via config.toml)

Supabase sends a reauthentication OTP email internally when a user attempts a sensitive action. There is no `[auth.email.template.reauthentication]` key in config.toml — this email cannot be customized through the template system. You can still create a React Email component for it for preview/documentation purposes.

- **CTA**: Displays OTP code `{{ .Token }}` — **no `{{ .ConfirmationURL }}` available**
- **Variables**: `{{ .Token }}`, `{{ .SiteURL }}`, `{{ .Email }}`, `{{ .Data }}`

---

## Notification Templates

These are informational security alerts — no CTA needed. Configured via `[auth.email.notification.<type>]` in config.toml. All require `enabled = true`.

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

---

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

---

## PKCE Flow

For server-side auth frameworks (Next.js App Router, SvelteKit, Remix), you may need to use PKCE-compatible URLs instead of `{{ .ConfirmationURL }}`. Replace the button href with a constructed URL using `{{ .TokenHash }}`:

```
{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=<type>&redirect_to={{ .RedirectTo }}
```

The `type` parameter changes per template:

| Template | Type Value |
| --- | --- |
| confirmation | `email` |
| invite | `invite` |
| magic_link | `magiclink` |
| email_change | `email_change` |
| recovery | `recovery` |

**Example — PKCE confirmation button:**

```tsx
<Button
  href="{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=email&redirect_to={{ .RedirectTo }}"
  className="box-border bg-gray-900 text-white px-6 py-3 text-sm font-medium no-underline"
>
  Confirm Email
</Button>
```

Use the PKCE approach when your app handles the token exchange server-side (e.g., Next.js `/auth/confirm` route that calls `supabase.auth.verifyOtp()`). Use `{{ .ConfirmationURL }}` when Supabase handles the redirect directly.
