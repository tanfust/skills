# Next.js App Router notes

Constraints met while shipping the surfaces on Next.js 16 with `cacheComponents: true`. Each one failed quietly, not loudly, which is why they are written down. Skip this file on another framework; the procedure in SKILL.md does not depend on it.

- [Staticness is verified in the build output](#staticness-is-verified-in-the-build-output)
- [Route handlers](#route-handlers)
- [Negotiation lives in the proxy, not the page](#negotiation-lives-in-the-proxy-not-the-page)
- [Headers](#headers)
- [Adding a mirrored page](#adding-a-mirrored-page)

## Staticness is verified in the build output

Every agent surface should be prerendered: `llms.txt`, `/md/*`, `robots.txt`, the api-catalog, the OpenAPI document, the server card. In the `next build` table each should print `○ (Static)` or `● (SSG)`. A `ƒ` means something in the handler read request data or awaited IO and the route became a function invocation on every hit. Expected exceptions: the MCP endpoint itself (it reads JSON-RPC bodies) and any handler that must export `OPTIONS` for CORS.

With `cacheComponents` on, the `dynamic` and `dynamicParams` segment configs are rejected outright, so there is no directive to lean on; the only safeguard is not reading request data, and checking the build table.

## Route handlers

- All filesystem reads are `readFileSync` at module scope. An awaited read inside the handler bails it out of prerendering.
- Exporting `POST`, `PUT`, `PATCH`, `DELETE` or `OPTIONS` from a route costs it its prerender. `HEAD` is derived from `GET` and is free. Un-exported `OPTIONS` is auto-implemented as `204` with an `Allow` header but without `Access-Control-Allow-*`, so a card that browsers fetch cross-origin has to export `OPTIONS` and accept being dynamic.
- To opt a handler out of prerendering on purpose, `await connection()` at the top, not a segment config.
- `notFound()` inside a route handler returns a null body with no `Content-Type`. The markdown 404 is built by hand so an agent that asked for markdown gets markdown, with a heading and recovery links, and `X-Robots-Tag: noindex`. That body must be synchronous and free of request data, because an unknown slug is served through the prerender path at request time; awaited IO or a clock read there throws in production and never at build.
- A catch-all `app/api/[...path]/route.ts` sorts last among `/api` matchers and turns every unknown API path, at any depth and for every method, into the JSON error envelope. It exports all methods; it can afford to because it has no `generateStaticParams` and so has no prerender to lose. Never add `generateStaticParams` to it.

## Negotiation lives in the proxy, not the page

Reading `Accept` inside a page turns every HTML request into a function invocation. Instead the proxy (middleware) rewrites a GET whose `Accept` list contains the literal token `text/markdown` to the prerendered `/md/<slug>`. The two paths are then independent cache entries, so a browser and an agent can never receive each other's representation at any cache layer.

```ts
function wantsMarkdown(request: NextRequest): boolean {
  if (request.method !== "GET") return false;          // a POST to / must never become a markdown GET
  const accept = request.headers.get("accept");
  if (!accept) return false;
  return accept.split(",").some((part) => part.split(";")[0].trim().toLowerCase() === "text/markdown");
}
```

Literal token test, never RFC 9110 negotiation: every browser sends `*/*;q=0.8`, and a conformant negotiator would serve them markdown. The markdown routes set `Vary: Accept` on their own responses.

Exclude from the proxy matcher: the webhook routes, `/api/*`, `/md/*`, `/.well-known/*`, `llms.txt`, `robots.txt`, `sitemap.xml`, and static assets. No API route reads the session, and an unbounded space of made-up URLs should not cost one session round trip each.

## Headers

- Never put `Vary` in `next.config` `headers()`. A config entry replaces rather than appends, so it would clobber Next's `Vary: rsc, next-router-*` and break RSC navigation caching. Set `Vary: Accept` on the markdown responses themselves.
- The home page `Link:` header (api-catalog, service-desc, service-doc, describedby, alternate) is set in `next.config` `headers()`; that is fine, only `Vary` is special.
- Never add a bot-detection check to an agent-facing route. Enable it globally if you use it; enforce per route on the forms that need it, and say in `/auth.md` what agents cannot do.

## Adding a mirrored page

Six places, and the build catches most omissions when the route map asserts both directions:

1. The exact-path map in `lib/markdown/routes.ts`.
2. A renderer, a branch in `renderMarkdown()`, an entry in `markdownRoutes()`, and a module-scope `readFileSync` if the page is backed by MDX.
3. `app/sitemap.ts`, the `llms.txt` builder, and the `alternate` Link header config.

`markdownRoutes()` asserts at build time that every proxy target has a renderer and every renderer has a proxy target. The second direction used to pass silently and 404 in production for any agent that negotiated markdown on the page.
