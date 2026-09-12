# Skills Framework

The rules that decide what gets into this repo, how it is written, and when it is done. Read this before adding, moving, or reviewing a skill. It applies to skills written by hand and to skills proposed by an agent.

## What a Tanfust skill is

A procedure for a piece of work that has been done in production at least three times, covering the part where the vendor's documentation stops and the sequencing starts, ending in a check that proves the work landed.

That sentence is the whole standard. Everything below is it, expanded.

## Admission: the five tests

A skill ships only if it passes all five. Four out of five is a rejection, not a compromise.

### 1. Procedure, not documentation

If an agent gets the task right by fetching the official docs, the skill is noise and actively harms the pack by diluting it.

Vendors write reference material: what the function signature is, what the config key does. They do not write the order of operations, the thing that breaks on step four, or what to do when the error message names the wrong cause. That gap is the skill.

Test: name one thing in the draft that is not in the vendor docs and that cost real time to learn. If nothing qualifies, stop.

### 2. Done three times in production

Skills are extracted, not invented. A procedure written from reading rather than shipping will be confidently wrong in exactly the places that matter, and there is no way to tell from the inside.

Test: name the three projects. If two of them are the same codebase at different times, that counts as one.

### 3. The failure is silent or expensive

The best skills cover work where getting it wrong does not throw. A wrong RLS policy returns rows. A wrong webhook handler charges twice. A wrong email template lands in spam. Nobody finds out for weeks.

Where failure is loud and immediate, the agent will iterate its way to the answer without help, and the skill earns nothing.

Test: describe how the mistake reaches a customer. If the answer is "the build fails", skip it.

### 4. Narrow enough to name in three words

`supabase-auth-emails` passes. `supabase-helper` does not. A broad name means a broad skill, which means the description matches everything, which means it triggers on tasks it cannot help with and burns context.

Narrow also means winnable. Vendors own the broad terms and always will.

Test: could the name be a section heading in someone's documentation? Good. Could it be the title of the whole documentation site? Too broad.

### 5. It ends in verification

Every skill defines how the agent proves the result: a query that must return zero rows, a replayed webhook, a rendered email opened in a client, a request that must be rejected.

This is the test that most skills in the wild fail, and it is the one that makes this pack worth installing. An agent that reports "done" without evidence is the single most expensive behaviour in agentic development.

Test: read the last section. If it does not tell the agent what to run and what result means pass, the skill is not finished.

## Anti-patterns

Rejected on sight, regardless of quality:

- **Doc wrappers.** A restatement of a vendor's getting-started guide.
- **Best-practices skills that fight official packs.** Supabase, Prisma, Firebase, shadcn and Vercel publish their own. Competing on their home ground loses, and the pack looks derivative.
- **Personality and style skills.** They install well and teach nothing. Not this pack's positioning.
- **Aspirational skills.** Procedures for work not yet shipped. See test 2.
- **Kitchen-sink skills.** One skill covering auth, storage, and payments. Split it or drop it.
- **Skills that need the product to work.** A free skill that is a demo for a paid boilerplate is an advertisement, and readers can tell. The skill must be complete on its own.

## Anatomy

```
skills/<skill-name>/
├── SKILL.md            required
├── references/         loaded on demand, when the body would otherwise exceed its budget
│   └── <TOPIC>.md
├── scripts/            only for deterministic work an agent should not reimplement
└── assets/             templates, fixtures
```

Rules:

- Directory name, frontmatter `name`, and any marketplace entry must match exactly. A mismatch breaks installation silently, which is the worst kind of breakage.
- Lowercase kebab-case throughout.
- SKILL.md stays under 500 lines and aims for 150 to 250. Past that, move detail into `references/` and point at it from the body with a line saying when to read it.
- Reference files over 300 lines get a table of contents at the top.
- When a skill covers several variants of the same procedure (frameworks, cloud providers, payment processors), organize `references/` by variant so only the relevant one is read.

## Frontmatter

```yaml
---
name: skill-name-matching-directory
description: What it does, then every context where it should trigger.
---
```

The description is the only thing an agent sees before deciding to load the skill, so it is the whole triggering mechanism. Two failure modes, and undertriggering is by far the more common:

- **Undertriggering**: the skill exists and never fires, because the description describes the topic rather than the situations. Fix by listing the concrete nouns a user would actually type: table names, error codes, product names, file names.
- **Overtriggering**: it fires on unrelated work and wastes context. Fix by naming the boundary in the description itself.

Write it pushy. "Use this whenever the work touches X, Y or Z, even when the request sounds like a simple W" is correct and normal. All the when-to-use information lives here, never in the body.

## Writing style

- Imperative. "Wrap `auth.uid()` in a subquery", not "it is recommended that one wraps".
- Explain why a rule exists rather than shouting MUST. An agent that understands the reason generalizes to the case the skill did not anticipate; an agent following a rule does not.
- Lead each section with the failure it prevents.
- Include the error messages and SQLSTATE codes verbatim where they exist. People paste error text, and a skill that matches on it earns its place immediately.
- A failure-mode table near the end, mapping symptom to cause, is the highest-value 15 lines in most of these skills.
- No em dashes. Short sentences. Plain words.
- State where the skill stops. A skill that pretends to cover adjacent territory gets trusted on it, which is how bad advice ships.

## The verification section

Required. It is the last section of every SKILL.md and it answers three questions:

1. What command or query does the agent run?
2. What result counts as pass?
3. What does the agent report, in what shape?

Prefer checks that return nothing when clean, so any output is a finding. Prefer a report shaped as a list of concrete violations over a summary, because summaries let an agent hedge.

Where the check needs fixtures or a harness, put it in `references/` rather than the body.

## Naming

- `<vendor>-<noun>-<qualifier>`: `supabase-multi-tenant-rls`, `supabase-auth-emails`, `paddle-webhooks`.
- The vendor prefix is deliberate. It matches how people search and how directories categorize.
- No version numbers in names. Version the pack, not the skill.
- No `-helper`, `-utils`, `-pro`, `-ultimate`.

## Review rubric

Use this when evaluating a candidate, whether it is new or being moved in from elsewhere. Score each test pass or fail, then take the verdict.

| # | Test | Pass means |
| --- | --- | --- |
| 1 | Procedure not documentation | At least one named thing that is not in the vendor docs |
| 2 | Three times in production | Three projects named |
| 3 | Silent or expensive failure | The path from mistake to customer is describable |
| 4 | Narrow name | Three words, one seam |
| 5 | Ends in verification | Command, pass condition, report shape all present |

Verdicts:

- **Move as-is**: five passes, format already conforms.
- **Move with rewrite**: passes 1 to 4, fails 5, or format does not conform. Name what must change.
- **Merge**: passes the tests but overlaps an existing skill by more than roughly a third. Name the target skill.
- **Split**: passes 1 to 3, fails 4. Name the resulting skills.
- **Reject**: fails 1, 2 or 3. These are not fixable by editing.

A rejection is cheap and reversible. A weak skill in a small pack is not: the pack is judged on its worst entry, because that is the one a first-time visitor happens to open.

## Lifecycle

1. **Extract.** Write the draft from a real codebase with the code open, not from memory.
2. **Test.** Write two or three prompts a real user would type, run an agent with the skill and without it, and compare. If the outputs match, the skill is not adding anything. Keep the prompts in `evals/`.
3. **Cut.** Remove everything the agent got right without the skill. What remains is the skill.
4. **Ship.** Tag the pack, push, smoke-test both install paths.
5. **Revisit on breakage.** When the vendor changes something the skill assumed, fix the skill in the same session. A stale procedure is worse than none, because it is trusted.

## Scope of the pack

This repo covers the seams in shipping a production SaaS: tenancy and data access, payments and entitlements, transactional email, and making a product legible to agents.

It does not cover general engineering methodology, code style, project management, or anything an agent already does competently. Those are other people's packs and they are better at them.
