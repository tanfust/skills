---
name: supabase-auth-emails
description: Use when customizing Supabase Auth emails with React Email components. Covers all Supabase Auth email types — 5 auth action templates (confirmation, invite, magic link, recovery, email change) and 7 notification templates (password changed, email changed, phone changed, identity linked/unlinked, MFA enrolled/unenrolled), the shared layout wrapper, Tailwind styling for email, the build-to-HTML pipeline with Go template variables, and Supabase config.toml integration. Use this skill whenever the user mentions Supabase auth emails, custom email templates for Supabase, password reset emails, magic link emails, sign-up confirmation emails, MFA notification emails, or any work involving rendering React Email to static HTML for Supabase's template system. Also applies when adding new Supabase auth email types or connecting React Email output to Supabase local dev.
license: MIT
metadata:
  author: Wassim
  version: "1.2.0"
---

# Supabase Auth Email Templates with React Email

Customize all Supabase Auth emails using React Email components, rendered to static HTML for Supabase's Go-based template system. This skill works alongside the `react-email` skill — use that skill for general React Email component usage, and this one specifically for the Supabase Auth integration layer.

Read `references/TEMPLATES.md` for the full per-template variable reference and complete Go template variable listing.

## Theme & Branding Discovery

**Before generating any email template**, read the user's project to extract their existing theme and branding. Emails must visually match the app — never use generic hardcoded colors.

### 1. Read CSS / theme files

Search for `globals.css`, `global.css`, `tailwind.config.ts`, `tailwind.config.js`, or any theme token files. Extract:

- **CSS custom properties**: `--primary`, `--background`, `--foreground`, `--muted`, `--muted-foreground`, `--border`, `--accent`, and font families
- **Tailwind config**: `theme.extend.colors`, `theme.extend.fontFamily`, and any custom color palette

### 2. Read site config files

Search for `config/site.ts`, `lib/config.ts`, `src/config.ts`, or similar. Extract:

- App name, tagline, support email, base URL
- Logo URL if available
- Fall back to `package.json` `name` field if no site config exists

### 3. Map discovered values to email styles

| Theme Token | Maps To |
| --- | --- |
| `primary` | CTA button background, link color |
| `background` / `foreground` | Email body background, heading & body text color |
| `muted` / `muted-foreground` | Footer text, disclaimer text |
| `border` | HR dividers |
| Font family | `font-sans` override or inline `fontFamily` style |
| App name / support email | Layout header, footer |

### 4. Fallback

If no theme files exist in the project, use the generic defaults shown in the examples below.

## Prerequisites

React Email must be installed in the project. If it isn't, follow the manual setup:

```bash
# Install React Email and components
npm install @react-email/components
npm install react-email --save-dev

# Add preview script to package.json
# "email:dev": "email dev --dir emails --port 3000"
```

See the `react-email` skill or <https://react.email/docs/getting-started/manual-setup> for full setup instructions, tsconfig requirements, and component documentation.

You also need a Supabase project initialized (`supabase init`) with a `supabase/config.toml` file.

## How It Works

Supabase Auth sends emails for auth actions (sign-up confirmation, password reset, etc.) and security notifications (password changed, MFA enrolled, etc.). By default these use plain built-in templates. To customize them:

1. Write React Email components in `emails/` with typed props
2. A build script renders each component to static HTML, injecting Supabase's Go template variables (`{{ .ConfirmationURL }}`, `{{ .Email }}`, etc.) as prop values
3. The HTML files land in `supabase/templates/`
4. `supabase/config.toml` points each auth email type to its HTML file

This gives you the React Email dev preview for design iteration, while Supabase gets the static HTML it needs.

## Supabase Auth Email Types

Supabase supports 12 customizable email types via config.toml, across two categories:

### Auth Action Templates (5) — configured via `[auth.email.template.<type>]`

These emails contain a link the user must click to complete an action.

| Supabase Type | Purpose | Key Variable |
| --- | --- | --- |
| `confirmation` | Verify email after sign-up | `{{ .ConfirmationURL }}` |
| `invite` | Invite user to create account | `{{ .ConfirmationURL }}` |
| `magic_link` | Passwordless sign-in link | `{{ .ConfirmationURL }}` |
| `email_change` | Verify new email after change | `{{ .ConfirmationURL }}` |
| `recovery` | Password reset link | `{{ .ConfirmationURL }}` |

> **Note on reauthentication**: Supabase sends a reauthentication OTP email internally, but there is no `[auth.email.template.reauthentication]` config key. You can still create a React Email component for it (useful for preview/documentation), but it cannot be customized via config.toml.

### Notification Templates (7) — configured via `[auth.email.notification.<type>]`

These are informational security alerts — no action link needed.

| Supabase Type | Purpose |
| --- | --- |
| `password_changed` | Password was changed |
| `email_changed` | Email address was changed |
| `phone_changed` | Phone number was changed |
| `identity_linked` | New identity provider linked |
| `identity_unlinked` | Identity provider removed |
| `mfa_factor_enrolled` | MFA method added |
| `mfa_factor_unenrolled` | MFA method removed |

## Recommended File Structure

```
emails/
  _components/
    email-layout.tsx              # Shared wrapper — all templates use this
  confirm-sign-up.tsx             # confirmation
  invite-user.tsx                 # invite
  magic-link.tsx                  # magic_link
  change-email.tsx                # email_change
  reset-password.tsx              # recovery
  reauthentication.tsx            # (React Email preview only — no config.toml key)
  notify-password-changed.tsx     # password_changed
  notify-email-changed.tsx        # email_changed
  notify-phone-changed.tsx        # phone_changed
  notify-identity-linked.tsx      # identity_linked
  notify-identity-unlinked.tsx    # identity_unlinked
  notify-mfa-added.tsx            # mfa_factor_enrolled
  notify-mfa-removed.tsx          # mfa_factor_unenrolled

scripts/
  build-email-templates.ts        # Renders React Email → static HTML

supabase/
  templates/                      # Generated HTML — do NOT edit directly
  config.toml                     # Template path configuration
```

The `_components/` prefix is a React Email convention — the preview server ignores directories starting with `_`, so shared components don't appear as standalone previews.

## Shared Layout Component

Create a wrapper that provides consistent structure across all emails. Every template should use it.

**Always read the user's project first.** Import the app name, URL, and support email from the project's site config. For colors, read `globals.css` and `tailwind.config` to extract actual theme colors. See [Theme & Branding Discovery](#theme--branding-discovery).

```tsx
import {
  Body, Container, Head, Heading, Hr, Html, Link,
  Preview, Section, Tailwind, Text, pixelBasedPreset,
} from "@react-email/components";
// Import from the project's site config — adapt the path to the actual project
// import { siteConfig } from "@/config/site";

interface EmailLayoutProps {
  previewText: string;
  children: React.ReactNode;
}

export default function EmailLayout({ previewText, children }: EmailLayoutProps) {
  return (
    <Html lang="en">
      <Tailwind config={{ presets: [pixelBasedPreset] }}>
        <Head />
        <Preview>{previewText}</Preview>
        {/* bg-gray-100 → replace with project's background color */}
        <Body className="bg-gray-100 font-sans py-10">
          <Container className="mx-auto max-w-[560px] bg-white p-10">
            {/* Replace with siteConfig.name or project's app name */}
            {/* text-gray-900 → replace with project's foreground color */}
            <Heading className="text-2xl font-bold text-gray-900 text-center m-0">
              Your App Name
            </Heading>
            {/* border-gray-200 → replace with project's border color */}
            <Hr className="border-solid border-gray-200 my-6" />

            {children}

            <Hr className="border-solid border-gray-200 my-6" />
            {/* Footer — replace with siteConfig values */}
            {/* text-gray-500 → replace with project's muted-foreground color */}
            <Section className="text-center">
              <Text className="text-xs text-gray-500 m-0 mb-1">
                Your App Name — Your tagline here.
              </Text>
              <Text className="text-xs text-gray-500 m-0">
                Questions?{" "}
                <Link href="mailto:support@yourapp.com" className="text-gray-500 underline">
                  support@yourapp.com
                </Link>
              </Text>
            </Section>
          </Container>
        </Body>
      </Tailwind>
    </Html>
  );
}
```

When no centralized site config exists, make branding configurable via props:

```tsx
interface EmailLayoutProps {
  previewText: string;
  children: React.ReactNode;
  projectName?: string;
  logoUrl?: string;
  brandColor?: string;
  supportEmail?: string;
}
```

## Template Patterns

### Auth Action Email Pattern

Auth action emails include a CTA button linking to a Supabase confirmation URL, plus a raw URL fallback for email clients that strip buttons.

Replace the color classes below with the project's actual theme colors (see [Theme & Branding Discovery](#theme--branding-discovery)).

```tsx
import { Button, Heading, Section, Text } from "@react-email/components";
import EmailLayout from "./_components/email-layout";

interface ConfirmSignUpProps {
  confirmationUrl: string;
  email: string;
}

export default function ConfirmSignUp({ confirmationUrl, email }: ConfirmSignUpProps) {
  return (
    <EmailLayout previewText="Confirm your account">
      {/* text-gray-900 → foreground color */}
      <Heading as="h2" className="text-xl font-bold text-gray-900 m-0 mb-4">
        Confirm your email
      </Heading>
      {/* text-gray-700 → muted-foreground color */}
      <Text className="text-sm leading-6 text-gray-700 my-4">
        Please confirm your email address ({email}) by clicking the button below.
      </Text>
      <Section className="text-center my-8">
        {/* bg-gray-900 → primary color */}
        <Button
          href={confirmationUrl}
          className="box-border bg-gray-900 text-white px-6 py-3 text-sm font-medium no-underline"
        >
          Confirm Email
        </Button>
      </Section>
      {/* text-gray-500 → muted color */}
      <Text className="text-xs text-gray-500 my-4">
        If you didn't create an account, you can safely ignore this email.
      </Text>
      <Text className="text-xs text-gray-400 my-2 break-all">
        {confirmationUrl}
      </Text>
    </EmailLayout>
  );
}

ConfirmSignUp.PreviewProps = {
  confirmationUrl: "https://yourapp.com/auth/confirm?token=abc123",
  email: "user@example.com",
} satisfies ConfirmSignUpProps;
```

### Notification Email Pattern

Notification emails are simpler — no CTA button, just an explanation and a security callout linking to the password reset page.

Replace the color classes and URL below with the project's actual theme colors and site URL (see [Theme & Branding Discovery](#theme--branding-discovery)).

```tsx
import { Heading, Link, Text } from "@react-email/components";
import EmailLayout from "./_components/email-layout";

interface NotifyPasswordChangedProps {
  email: string;
}

export default function NotifyPasswordChanged({ email }: NotifyPasswordChangedProps) {
  return (
    <EmailLayout previewText="Password change notification">
      {/* text-gray-900 → foreground color */}
      <Heading as="h2" className="text-xl font-bold text-gray-900 m-0 mb-4">
        Your password was changed
      </Heading>
      {/* text-gray-700 → muted-foreground color */}
      <Text className="text-sm leading-6 text-gray-700 my-4">
        The password for your account ({email}) was recently changed.
      </Text>
      <Text className="text-sm leading-6 text-gray-700 my-4">
        If you made this change, no further action is needed.
      </Text>
      <Text className="text-sm leading-6 text-gray-700 my-4">
        If you did not make this change, secure your account immediately by{" "}
        {/* Use the project's site URL — e.g., from siteConfig.url */}
        <Link
          href="https://yourapp.com/auth/forgot-password"
          className="text-gray-900 underline font-medium"
        >
          resetting your password
        </Link>.
      </Text>
    </EmailLayout>
  );
}

NotifyPasswordChanged.PreviewProps = {
  email: "user@example.com",
} satisfies NotifyPasswordChangedProps;
```

## Email Styling Rules

These rules come from email client limitations — violating them causes rendering bugs.

- **Use Tailwind** via `<Tailwind config={{ presets: [pixelBasedPreset] }}>` — the `pixelBasedPreset` converts all sizing to `px` because email clients don't support `rem`
- **No flexbox or grid** — use block flow, `text-center`, `mx-auto` for layout
- **Button**: always include `box-border` — prevents padding from overflowing the button width in Outlook
- **Hr**: always include `border-solid` — email clients don't inherit border type, so omitting it renders no visible line
- **No SVG or WEBP images** — these don't render in many email clients
- **No CSS media queries** (`sm:`, `md:`, `dark:`) — not supported in email

For full component reference and styling details, use the `react-email` skill.

## Supabase Go Template Variables

When the build script renders templates, it passes Go template variable strings as literal prop values:

| React Prop | Go Template Variable | Description |
| --- | --- | --- |
| `confirmationUrl` | `{{ .ConfirmationURL }}` | Auth action link (confirm, invite, magic link, recovery, etc.) |
| `token` | `{{ .Token }}` | OTP code (used in reauthentication) |
| `email` | `{{ .Email }}` | User's email address |
| — | `{{ .SiteURL }}` | Site URL from Supabase config (useful in footers) |

**Always use `{{ .ConfirmationURL }}`** for auth action template links. Supabase generates the correct URL regardless of your auth flow (including PKCE). Do not construct URLs manually using token hashes.

See `references/TEMPLATES.md` for the complete variable list per template, including notification-specific variables (`{{ .OldEmail }}`, `{{ .Provider }}`, `{{ .FactorType }}`, etc.).

## Build Script

The build script bridges React Email components and Supabase's static HTML templates. It imports each component, calls `render()` with Go template variable strings as props, and writes the output.

```typescript
import { render } from "@react-email/components";
import { writeFileSync, mkdirSync } from "fs";
import { join } from "path";

// Import all email components
import ConfirmSignUp from "../emails/confirm-sign-up";
// ... other imports

const outDir = join(import.meta.dirname, "..", "supabase", "templates");
mkdirSync(outDir, { recursive: true });

const SB = {
  confirmationUrl: "{{ .ConfirmationURL }}",
  token: "{{ .Token }}",
  email: "{{ .Email }}",
};

const templates = [
  { name: "confirm-sign-up", element: ConfirmSignUp({ confirmationUrl: SB.confirmationUrl, email: SB.email }) },
  // ... other templates with their respective Go template variables
];

async function build() {
  for (const { name, element } of templates) {
    const html = await render(element);
    writeFileSync(join(outDir, `${name}.html`), html, "utf-8");
    console.log(`  ${name}.html`);
  }
}

build().catch((err) => { console.error("Build failed:", err); process.exit(1); });
```

Add a package.json script to run it:

```json
{
  "scripts": {
    "email:build-templates": "npx tsx scripts/build-email-templates.ts"
  }
}
```

## Supabase config.toml Integration

Wire each template in `supabase/config.toml`. Only these keys are supported by the Supabase CLI:

### Auth action templates — `[auth.email.template.<type>]`

```toml
[auth.email.template.confirmation]
subject = "Confirm your account"
content_path = "./supabase/templates/confirm-sign-up.html"

[auth.email.template.invite]
subject = "You have been invited"
content_path = "./supabase/templates/invite-user.html"

[auth.email.template.magic_link]
subject = "Your sign-in link"
content_path = "./supabase/templates/magic-link.html"

[auth.email.template.email_change]
subject = "Confirm your new email"
content_path = "./supabase/templates/change-email.html"

[auth.email.template.recovery]
subject = "Reset your password"
content_path = "./supabase/templates/reset-password.html"
```

> There is no `[auth.email.template.reauthentication]` — Supabase handles that email internally.

### Notification templates — `[auth.email.notification.<type>]`

> **Path difference**: Notification `content_path` values use `./templates/` (relative to the `supabase/` directory), while auth action templates use `./supabase/templates/` (relative to project root). This matches Supabase's own conventions.

```toml
[auth.email.notification.password_changed]
enabled = true
subject = "Your password was changed"
content_path = "./templates/notify-password-changed.html"

[auth.email.notification.email_changed]
enabled = true
subject = "Your email was changed"
content_path = "./templates/notify-email-changed.html"

[auth.email.notification.phone_changed]
enabled = true
subject = "Your phone number was changed"
content_path = "./templates/notify-phone-changed.html"

[auth.email.notification.identity_linked]
enabled = true
subject = "New identity linked to your account"
content_path = "./templates/notify-identity-linked.html"

[auth.email.notification.identity_unlinked]
enabled = true
subject = "Identity unlinked from your account"
content_path = "./templates/notify-identity-unlinked.html"

[auth.email.notification.mfa_factor_enrolled]
enabled = true
subject = "MFA method added to your account"
content_path = "./templates/notify-mfa-added.html"

[auth.email.notification.mfa_factor_unenrolled]
enabled = true
subject = "MFA method removed from your account"
content_path = "./templates/notify-mfa-removed.html"
```

## Adding a New Template

1. Create `emails/my-template.tsx` following the auth action or notification pattern
2. Import it in `scripts/build-email-templates.ts` and add to the `templates` array with the correct Go template variable mapping
3. Add the corresponding `[auth.email.template.*]` or `[auth.email.notification.*]` block in `supabase/config.toml` (only if the type is supported — check the Supabase CLI config docs)
4. Run the build script to generate the HTML
5. Preview with the React Email dev server
6. Restart local Supabase for it to pick up the new template

## Verification

1. **Preview**: run the React Email dev server — all templates should appear and render
2. **Build**: run the build script — HTML files generated in `supabase/templates/`
3. **Local test**: restart local Supabase, trigger an auth flow (sign up, forgot password), check InBucket (typically at `localhost:54324`) for the custom-styled email
4. **Variable check**: open a generated HTML file and verify `{{ .ConfirmationURL }}` and `{{ .Email }}` appear as literal text (not rendered as empty)
