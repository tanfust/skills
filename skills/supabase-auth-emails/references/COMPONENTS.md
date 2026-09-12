# Layout and template components

Read this when writing a template from scratch. SKILL.md assumes this shape and only shows the build and configuration around it.

- [Project discovery before styling](#project-discovery-before-styling)
- [File layout](#file-layout)
- [Shared layout](#shared-layout)
- [Action email](#action-email)
- [Styling rules and why](#styling-rules-and-why)

## Project discovery before styling

Generic grey templates are the tell that an agent wrote the email without looking at the app. Before writing components, read:

- `globals.css` or `global.css` for CSS custom properties: `--primary`, `--background`, `--foreground`, `--muted`, `--muted-foreground`, `--border`, and the font stack.
- `tailwind.config.*` for `theme.extend.colors` and `theme.extend.fontFamily`.
- `config/site.ts`, `lib/config.ts` or similar for the app name, tagline, support address, base URL and logo. Fall back to `package.json` `name`.

Map them: `primary` to the button background and link colour, `background` and `foreground` to body and text, `muted-foreground` to footer text, `border` to rules, the font stack to an explicit `fontFamily`. Email clients do not load web fonts reliably, so the stack must end in a system font.

If nothing exists, make branding props on the layout (`projectName`, `logoUrl`, `brandColor`, `supportEmail`) rather than hardcoding placeholders that ship.

## File layout

```
emails/
  _components/
    email-layout.tsx        shared wrapper, every template uses it
  confirm-sign-up.tsx       confirmation
  magic-link.tsx            magic_link
  reset-password.tsx        recovery
  invite-user.tsx           invite
  change-email.tsx          email_change
scripts/
  build-email-templates.ts  renders the above to static HTML
supabase/
  templates/                generated, committed, never edited by hand
  config.toml
```

The `_components/` underscore prefix is a React Email convention: the preview server ignores directories starting with `_`, so shared parts do not appear as previews.

## Shared layout

Tailwind through the `<Tailwind>` component with `pixelBasedPreset`, which converts sizing to `px` because clients do not support `rem`. Inline `style` objects work equally well and are what a plain house style usually ends up as; pick one and do not mix.

```tsx
import {
  Body, Container, Head, Heading, Hr, Html, Link,
  Preview, Section, Tailwind, Text, pixelBasedPreset,
} from "@react-email/components";
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
        <Body className="bg-gray-100 font-sans py-10">
          <Container className="mx-auto max-w-[560px] bg-white p-10">
            <Heading className="text-2xl font-bold text-gray-900 text-center m-0">
              Your App Name
            </Heading>
            <Hr className="border-solid border-gray-200 my-6" />

            {children}

            <Hr className="border-solid border-gray-200 my-6" />
            <Section className="text-center">
              <Text className="text-xs text-gray-500 m-0 mb-1">
                Your App Name. Your tagline here.
              </Text>
              <Text className="text-xs text-gray-500 m-0">
                Questions?{" "}
                <Link href="mailto:support@example.com" className="text-gray-500 underline">
                  support@example.com
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

Replace every `gray-*` with the project's tokens from discovery. `Preview` sets the inbox snippet; leave it empty and clients show the first text in the body, which is usually the heading repeated.

## Action email

All five templated types have the same shape: a heading, one sentence of context, a button, a security line, and the raw URL as text for clients that strip button markup.

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
      <Heading as="h2" className="text-xl font-bold text-gray-900 m-0 mb-4">
        Confirm your email
      </Heading>
      <Text className="text-sm leading-6 text-gray-700 my-4">
        Confirm {email} by clicking the button below.
      </Text>
      <Section className="text-center my-8">
        <Button
          href={confirmationUrl}
          className="box-border bg-gray-900 text-white px-6 py-3 text-sm font-medium no-underline"
        >
          Confirm email
        </Button>
      </Section>
      <Text className="text-xs text-gray-500 my-4">
        If you did not create an account, ignore this email. Nobody can sign in without the link.
      </Text>
      <Text className="text-xs text-gray-400 my-2 break-all">{confirmationUrl}</Text>
    </EmailLayout>
  );
}

ConfirmSignUp.PreviewProps = {
  confirmationUrl: "https://example.com/auth/confirm?token_hash=abc123&type=email",
  email: "user@example.com",
} satisfies ConfirmSignUpProps;
```

`PreviewProps` hold realistic values for the preview server. The Go variables are injected by the build script, never here.

`email_change` additionally receives `newEmail` (`{{ .NewEmail }}`) and should show both addresses. `invite` should name who is inviting if the app passes it through `{{ .Data }}`; otherwise say which product.

## Styling rules and why

These come from email client behaviour. None of them errors; each one just renders wrong in a client you did not open.

| Rule | Because |
| --- | --- |
| No flexbox or grid; use block flow, `text-center`, `mx-auto` | Outlook desktop renders with the Word engine and ignores both |
| Pixel sizes only (`pixelBasedPreset`, or `px` in style objects) | `rem` is unsupported in several clients and falls back to browser defaults |
| `box-border` on `Button` | Without it Outlook adds the padding outside the width and the button overflows the container |
| `border-solid` on every `Hr` | Clients do not inherit border style; an unstyled rule is invisible |
| No `sm:`, `md:`, `dark:` variants | Media queries are stripped or ignored; Gmail on Android and Outlook do their own dark mode inversion |
| No SVG or WebP | Not rendered in Gmail and Outlook; use PNG hosted on a stable URL |
| Font stack ends in a system font | Web fonts load in Apple Mail and almost nowhere else |
| Raw URL as text under the button | Some clients and plain-text views strip the button markup entirely |
