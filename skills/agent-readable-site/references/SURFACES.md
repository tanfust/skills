# The surfaces, with their sources

What each agent-facing surface is, where the specification lives, and what an agent actually sends. Read 2026-09-12. Two of these are drafts and are marked as such; re-check them before relying on a field name.

- [llms.txt](#llmstxt)
- [Markdown negotiation](#markdown-negotiation)
- [Content-Signal in robots.txt](#content-signal-in-robotstxt)
- [Link headers and api-catalog](#link-headers-and-api-catalog)
- [MCP server card (draft)](#mcp-server-card-draft)
- [Scanners](#scanners)

## llms.txt

Source: <https://llmstxt.org/> (Jeremy Howard, first published 3 September 2024, revised 10 August 2026)

- Location: "at the site root, or at any path within it, covering the pages under that path". In practice `/llms.txt`.
- Format, in order: an optional byte-order mark; "An H1 with the name of the project or site. This is the only required section"; a blockquote summary; optional prose; then "Zero or more markdown sections delimited by H2 headers, containing 'file lists' of URLs". Each list item is "a required markdown hyperlink `[name](url)`, then optionally a `:` and notes".
- "The 'Optional' section is used, by convention, for secondary information: links an agent can skip when a shorter context is needed."
- Page mirrors: "Pages with information that agents might need provide a clean markdown version of those pages at the same URL as the original page, either with `.md` appended (`page.html.md`) or with the extension replaced by `.md` (`page.md`). (URLs without file names should append `index.html.md` or `index.md` instead.)"

The spec says nothing about generating the file. The procedure in SKILL.md generates it from the same data the pages render from, because a hand-written `llms.txt` is a second catalog and second catalogs drift.

## Markdown negotiation

Source: <https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/> (Cloudflare, feature announced 12 February 2026)

- The agent sends `Accept: text/markdown`.
- A converted response is `Content-Type: text/markdown; charset=utf-8` with `Vary: Accept` "to ensure caches store separate variants for markdown and HTML requests".
- `x-markdown-tokens` carries an "estimated number of tokens in the Markdown document".
- The document describes Cloudflare's edge conversion; it gives no origin-side rules, and it does not say how a mixed `Accept` with quality values is handled.

Origin-side, the following was established in production and is not in the document: every browser sends an `Accept` ending in `*/*;q=0.8`, so a conformant RFC 9110 negotiator will serve browsers markdown. Match the literal token `text/markdown` in the `Accept` list and nothing else. Never rewrite a non-GET. Serve the same document at a stable `/md/<slug>` path too, because not every client can set headers.

## Content-Signal in robots.txt

Source: <https://contentsignals.org/> (Content Signals Policy, published by Cloudflare), as reproduced in Cloudflare's managed robots.txt documentation <https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/>

- A `Content-Signal:` line under a `User-Agent:` group, listing `signal=yes|no` pairs separated by commas. Optionally a path prefix before the pairs, e.g. `Content-Signal: /blog search=yes, ai-train=no, ai-input=yes`.
- `search`: "building a search index and providing search results (e.g., returning hyperlinks and short excerpts from your website's contents)".
- `ai-input`: "inputting content into one or more AI models (e.g., retrieval augmented generation, grounding, or other real-time taking of content for generative AI search answers)".
- `ai-train`: "training or fine-tuning AI models".
- "If the website operator does not include a content signal for a corresponding use, the website operator neither grants nor restricts permission". Silence is not consent and not refusal; say what you mean for all three.
- The policy text Cloudflare injects includes the reservation of rights language referring to Article 4 of EU Directive 2019/790. Include the comment block from contentsignals.org if you want that reservation to be explicit.

A common working line for a product site that wants to be found and quoted but not trained on: `Content-Signal: search=yes, ai-input=yes, ai-train=no`.

## Link headers and api-catalog

Source: RFC 8288 (Web Linking), RFC 9727 (api-catalog well-known URI) and RFC 9264 (Linkset).

- `/.well-known/api-catalog` returns a linkset (`application/linkset+json`) whose entries point at the API's `service-desc` (the OpenAPI document) and `service-doc` (human documentation).
- The home page's `Link:` response header advertises the same relations, plus `describedby` for the OpenAPI document and `alternate; type="text/markdown"` for the markdown twin. Scanners read the header before they read the body.

## MCP server card (draft)

Source: SEP-1649, <https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1649>, status Draft as of the read date, opened 14 October 2025.

- Proposed location `/.well-known/mcp/server-card.json`.
- Proposed fields: `version` (card schema), `protocolVersion` (e.g. `2025-06-18`), `serverInfo` with `name`, `version` and optional `title`, `transport` with `type` and `endpoint`, `capabilities`, and optionally `description`, `documentationUrl`, `authentication`, and static or `dynamic` `tools`, `resources`, `prompts`.
- Because it is a draft, the field set can change. Generate the card and the server's `initialize` response from one object so they cannot disagree, and re-check the SEP when a scanner starts failing the card.

A card without a working server behind it is worse than no card. If you publish one, `tools/list` over Streamable HTTP must answer.

## Scanners

Two third-party scanners exercise these surfaces and are the closest thing to an external verifier.

- <https://isitagentready.com/>, operated by Cloudflare. Checks, per its own page: robots.txt, sitemap, Link headers, DNS-AID; markdown content negotiation; AI bot rules in robots.txt, Content Signals, Web Bot Auth; MCP server card, Agent Skills, WebMCP, API catalog, OAuth discovery, OAuth protected resource, auth.md, ARD manifest; and commerce protocols (x402, MPP, UCP, ACP). It has a scan endpoint, `POST https://isitagentready.com/api/scan` with a JSON body `{"url": ...}`, which is how the production site is checked after deploy.
- <https://is-agentic.com/>, operated by Vercel and Ora. Scores 0 to 100 from "essential checks" (server-rendered content, correct HTTP behaviour, document structure, recoverable errors, usable controls) and "recommended checks" that only apply if the site offers APIs, OAuth, MCP or commerce. Reports include "an observed agent journey".

Neither scanner is a specification. A green check is evidence that the surface is reachable and well-formed on the day of the scan, not that it is correct. The curl script in `scripts/verify-agent-surface.sh` is the check you own.
