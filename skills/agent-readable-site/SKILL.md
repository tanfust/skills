---
name: agent-readable-site
description: Make a marketing or product site legible to AI agents and prove it, with an llms.txt generated from the same data the pages render from, a markdown mirror under /md/ with Accept text/markdown negotiation that never catches browsers, a robots.txt Content-Signal line, Link headers, 404s that answer in the format the client asked for, and optionally an MCP server card with a read-only server behind it. Use this whenever the work touches llms.txt or llms-full.txt, Accept text/markdown or Markdown for Agents, Content-Signal or ai-train in robots.txt, agent readiness or "agent-ready", isitagentready.com or is-agentic.com scores, api-catalog or .well-known files, an MCP server on a website, JSON errors for unknown API paths, or making docs and pricing readable by ChatGPT, Claude or Perplexity. Reach for it even for "just add an llms.txt", because a hand-written index drifts within a month and nobody notices. Not for SEO in general, structured data alone, or an MCP server over an authenticated product API.
license: MIT
---

# Agent-readable site

An agent that lands on a marketing site gets a React shell, a 404 page it cannot parse, or a hand-written `llms.txt` that lists a pricing page you rebuilt in March. None of that logs an error. The site looks fine in a browser and is invisible or wrong to the thing that increasingly sends the traffic. This skill is the set of surfaces a public site publishes for agents, the constraints that make them correct rather than merely present, and a script that asserts the whole contract against a running server.

Specifications and their sources are in `references/SURFACES.md`; two of the surfaces are drafts and the file says which. Framework-specific constraints met in production are in `references/NEXTJS.md`. The executable check is `scripts/verify-agent-surface.sh`.

## Order of work

1. Decide what agents may and may not do, and write it down
2. Generate `llms.txt` from the data the pages already use
3. Publish a markdown mirror and negotiate on `Accept` without catching browsers
4. State your position in `robots.txt` with Content-Signal
5. Advertise the surfaces in `Link:` headers and answer 404s in the client's format
6. Optionally, an MCP server card with a server that actually answers
7. Verify with the script and the two scanners

## 1. Decide what agents may do

Before publishing anything, write `/auth.md` (and mirror it at `/.well-known/auth.md`): what is public, what needs a human (checkout with a card, newsletter sign-up behind bot detection), and what does not exist (no OAuth, no write tools). Publishing OAuth discovery documents for an authorization server you do not have is worse than silence, because an agent will try to complete a flow that cannot complete. The same rule governs every surface below: publish what works end to end, nothing else.

## 2. Generate `llms.txt`

Follow llmstxt.org: an H1 with the site name (the only required element), a blockquote summary, then H2 sections of `- [name](url): note` lines, with an `Optional` section for what an agent can skip. Build it from the same modules that render the catalog, blog and docs, so a new product or a renamed page appears in it on the next build without anyone remembering. Prefer absolute URLs. Point at the markdown twins (`/md/...`) rather than HTML pages where twins exist, and say once at the top that any content page also returns markdown on request.

Include the things an agent would otherwise guess at: which endpoints need no API key, that prices are or are not published, where the agent boundary document is.

## 3. Publish a markdown mirror and negotiate

Two entry points to one document: a stable path (`/md/<slug>`) for clients that cannot set headers, and content negotiation on the HTML URL for clients that can. Responses are `text/markdown; charset=utf-8` with `Vary: Accept`, and an `x-markdown-tokens` header with an estimated token count is the convention Cloudflare set and agents have started to read.

Negotiation is where sites break. Every browser sends an `Accept` that ends in `*/*;q=0.8`, so a correct RFC 9110 negotiator serves browsers markdown. Do not negotiate; test for the literal token `text/markdown` in the `Accept` list, GET only, and rewrite to the `/md/` twin. Serve the twin from a prerendered path so the HTML and markdown representations are separate cache entries and can never be served to the wrong client by an intermediate cache. Keep `/md/` out of search indexes (`Disallow: /md/` in robots.txt, `X-Robots-Tag: noindex` on the responses) so the mirror does not compete with the pages as duplicate content.

Do not mirror a page whose content is wrong or placeholder. A machine-readable copy of a stale pricing page ships wrong facts to every agent at once; leave it out until the page is fixed.

## 4. State your position in `robots.txt`

Add a `Content-Signal:` line under `User-Agent: *` that names all three signals, because an omitted signal "neither grants nor restricts permission". For a site that wants to be found and quoted but not trained on, that is `Content-Signal: search=yes, ai-input=yes, ai-train=no`. Keep the `Sitemap:` line, and disallow the paths that only make sense with a session (`/account/`, `/auth/`, single-use download links). Robots directives are requests, not enforcement; the point of the line is that your position is stated where crawlers look for it, and that the scanners can read it.

## 5. Advertise, and fail in the right format

The home page sends a `Link:` header with `rel="alternate"; type="text/markdown"` pointing at its twin and, if there is an API, `rel="api-catalog"`, `service-desc` (the OpenAPI document) and `service-doc` (the human docs). Scanners read the header before the body.

A 404 is the most common response an agent will ever get from a site, so treat it as a response rather than a dead end. The HTML 404 links the sitemap, `llms.txt` and the docs. An unknown `/md/` slug answers `404` in markdown, with a heading and the same links. Every unknown path under `/api/`, at any depth and for any method, answers in JSON with one envelope (`error` code, `message`, `status`, a `hint` naming the endpoint that lists valid values, a `documentation` link). Without the catch-all, an agent that guesses `/api/v1/product/123` gets an HTML page.

## 6. Optionally, an MCP server

Only if there is something read-only worth exposing, such as a product catalog. Publish the card at `/.well-known/mcp/server-card.json` following SEP-1649 (still a draft; check the field names against the SEP when a scanner complains), and generate the card and the server's `initialize` response from one object. The server must answer `tools/list` over Streamable HTTP; a card with no server behind it fails louder than no card. No write tools on a marketing site: nothing there is something an agent could correctly mutate.

## Failure modes worth recognizing quickly

| Symptom | Cause |
| --- | --- |
| Browsers get a markdown document | Negotiation honours `*/*;q=0.8`; test for the literal `text/markdown` token instead |
| A `POST` to `/` returns a markdown page | The rewrite did not check the method |
| Markdown twin 404s in production, worked locally | A page was added to the negotiation map but no renderer, or the reverse; assert both directions at build |
| Agents cite a product that no longer exists | `llms.txt` is hand-written; generate it |
| Duplicate-content warnings in Search Console | `/md/` is indexable; disallow it and set `noindex` |
| Scanner says "no markdown negotiation" although `/md/` works | `Vary: Accept` missing, or the `Accept` header check runs after a cache that already stored HTML |
| Scanner flags OAuth discovery as broken | Discovery documents published for an authorization server that does not exist; remove them and say so in `/auth.md` |
| An agent hits `/api/whatever` and receives HTML | No JSON catch-all under `/api/` |
| MCP card present, `tools/list` fails | Card generated separately from the server, or the endpoint is behind bot detection or session middleware |
| Everything green locally, scanner fails on the deployed site | Edge or CDN strips `Link` or `Vary`, or serves a cached HTML variant for the markdown request |

## 7. Verify

Run the script against the deployed host, not localhost, because caches and edges are part of what is being tested:

```bash
BASE=https://www.example.com MD_SLUG=home HTML_PAGE=/ ./scripts/verify-agent-surface.sh
```

It asserts, with one line per check: `llms.txt` is served, starts with an H1, has a blockquote and link lists, and every same-host link in it resolves; `/md/<slug>` is served as `text/markdown; charset=utf-8`, negotiation on the HTML page returns the same type, the response varies on `Accept`, a browser `Accept` still gets `text/html`, a `POST` with `Accept: text/markdown` is not rewritten, and an unknown `/md/` slug 404s in markdown with recovery links; `robots.txt` carries a `Content-Signal` line stating all three signals and a `Sitemap` line; the home page `Link` header advertises the markdown alternate (and the api-catalog when one exists); unknown pages are real 404s that point at `llms.txt`, and unknown `/api/` paths answer JSON with an `error` code; and, when configured, the MCP card is served with `serverInfo` and a transport `endpoint`, and `tools/list` answers through the MCP inspector.

Pass: the script prints `N passed, 0 failed` and exits 0. Any `FAIL` line is a finding with the check, the expected value and the observed value in it. Remove checks for surfaces the site deliberately does not have rather than leaving them red; a green run has to mean something.

Then run both scanners, which exercise the surfaces from outside your network and catch what an edge cache does to them:

```bash
curl -s -X POST https://isitagentready.com/api/scan -H 'Content-Type: application/json' \
  -d '{"url":"https://www.example.com"}' | jq
```

and <https://is-agentic.com/> for the same URL. Pass: every check that corresponds to a surface you published is green on isitagentready.com, and is-agentic.com's essential checks pass. Do not chase a score by publishing surfaces you cannot back (OAuth, commerce protocols); step 1 decides what you publish, the scanners only confirm it is reachable.

Report as a table of `check / expected / observed`, one row per script line that failed or was deliberately skipped, followed by the two scanner results with their report URLs and the date. If the script is green and the scanners agree, say so and list the surfaces that were checked, so the next person can tell a verified site from one that looked fine in a browser.

## Where this stops

This skill covers the public, unauthenticated surface of a site. It does not cover an MCP server over an authenticated product API, OAuth for agents, agent commerce protocols, DNS-based discovery (DNS-AID needs SVCB records in a signed zone, which most DNS hosts cannot do yet), or search engine optimisation as such. Structured data (JSON-LD) helps agents too and is worth doing; it is a well-documented topic elsewhere and not repeated here.
