# Supabase Auth Emails Skill

An agent skill for customizing all Supabase Auth emails using React Email components.

## What It Does

Guides you through creating custom email templates for every Supabase Auth email type — sign-up confirmations, magic links, password resets, invitations, and 7 security notification types. Templates are built as React Email components with Tailwind CSS, then rendered to static HTML with Supabase's Go template variables for local and production use.

## Structure

```
supabase-auth-emails/
├── SKILL.md              # Main skill — patterns, config, build pipeline
├── README.md             # This file
└── references/
    └── TEMPLATES.md      # Per-template variable reference
```

## Covers

- Project theme discovery (colors, fonts, brand config) for email styling
- Shared email layout wrapper component
- 5 auth action email patterns (with CTA buttons)
- 7 notification email patterns (informational)
- Tailwind CSS styling rules for email clients
- Supabase Go template variable mapping
- Build script (React Email to static HTML)
- `supabase/config.toml` integration
- Adding new email types

## Prerequisites

- React Email (`@react-email/components`) — see the `react-email` skill or <https://react.email/docs/getting-started/manual-setup>
- Supabase project with `supabase/config.toml`
- TypeScript + tsx for the build script

## Usage

The skill triggers automatically when working with Supabase auth emails, email templates, or the `emails/` directory. It works alongside the `react-email` skill for component-level details.
