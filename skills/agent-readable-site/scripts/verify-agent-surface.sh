#!/usr/bin/env bash
#
# Asserts the agent-facing contract of a site against a running server.
# Read-only. Exits non-zero on any failure. Prints one line per check.
#
#   BASE=https://www.example.com ./verify-agent-surface.sh
#
# Tune the lists below to the site. Anything not present on the site should be
# removed from the list rather than left to fail; the point is a green run that
# means something.

set -uo pipefail

BASE="${BASE:-http://localhost:3000}"
MD_SLUG="${MD_SLUG:-home}"                  # a slug that exists under /md/
HTML_PAGE="${HTML_PAGE:-/}"                 # a page that has a markdown twin
API_404="${API_404:-/api/nope}"             # any path under /api that does not exist; set empty to skip
MCP_CARD="${MCP_CARD:-/.well-known/mcp/server-card.json}"   # set empty to skip
MCP_ENDPOINT="${MCP_ENDPOINT:-/api/mcp}"    # set empty to skip

pass=0; fail=0
ok()  { printf '  ok    %s\n' "$1"; pass=$((pass+1)); }
bad() { printf '  FAIL  %s\n        expected: %s\n        actual:   %s\n' "$1" "$2" "$3"; fail=$((fail+1)); }
expect()   { [ "$2" = "$3" ] && ok "$1" || bad "$1" "$2" "$3"; }
contains() { case "$3" in *"$2"*) ok "$1" ;; *) bad "$1" "contains '$2'" "$(printf '%s' "$3" | head -c 120)" ;; esac; }
status() { curl -sS -o /dev/null -w '%{http_code}' "$@"; }
ctype()  { curl -sS -o /dev/null -w '%{content_type}' "$@"; }
header() { curl -sSI "$2" | tr -d '\r' | grep -i "^$1:" | head -1; }

echo "-> $BASE"

echo; echo "1. llms.txt"
expect "llms.txt is served" 200 "$(status "$BASE/llms.txt")"
llms="$(curl -sS "$BASE/llms.txt")"
expect "llms.txt starts with an H1" "#" "$(printf '%s' "$llms" | head -c 1)"
contains "llms.txt has a blockquote summary" $'\n> ' "$llms"
contains "llms.txt has at least one link list" "](http" "$llms"
# every absolute link in llms.txt that points at this host must resolve
while read -r url; do
  [ -z "$url" ] && continue
  path="${url#"$BASE"}"; [ "$path" = "$url" ] && continue      # skip links to other hosts
  expect "llms.txt link resolves: $path" 200 "$(status -L "$BASE$path")"
done < <(printf '%s' "$llms" | grep -oE '\]\((https?://[^) ]+)' | sed 's/](//' | sort -u)

echo; echo "2. Markdown mirror and negotiation"
expect "/md/$MD_SLUG is served" 200 "$(status "$BASE/md/$MD_SLUG")"
expect "/md/$MD_SLUG is markdown" "text/markdown; charset=utf-8" "$(ctype "$BASE/md/$MD_SLUG")"
expect "negotiated markdown on $HTML_PAGE" "text/markdown; charset=utf-8" "$(ctype -H 'Accept: text/markdown' "$BASE$HTML_PAGE")"
contains "negotiated response varies on Accept" "accept" "$(header vary "$BASE/md/$MD_SLUG" | tr 'A-Z' 'a-z')"
expect "browser Accept still gets HTML" "text/html; charset=utf-8" \
  "$(ctype -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' "$BASE$HTML_PAGE")"
post_status="$(status -X POST -H 'Accept: text/markdown' "$BASE$HTML_PAGE")"
case "$post_status" in 405|403|404) ok "POST with Accept: text/markdown is not rewritten ($post_status)" ;; *) bad "POST with Accept: text/markdown is not rewritten" "405/403/404" "$post_status" ;; esac
expect "unknown /md slug is 404" 404 "$(status "$BASE/md/no-such-document-xyz")"
expect "unknown /md slug answers in markdown" "text/markdown; charset=utf-8" "$(ctype "$BASE/md/no-such-document-xyz")"
contains "markdown 404 links llms.txt" "/llms.txt" "$(curl -sS "$BASE/md/no-such-document-xyz")"

echo; echo "3. robots.txt and Content-Signal"
expect "robots.txt is served" 200 "$(status "$BASE/robots.txt")"
robots="$(curl -sS "$BASE/robots.txt" | tr 'A-Z' 'a-z')"
contains "robots.txt carries a Content-Signal line" "content-signal:" "$robots"
for sig in search ai-input ai-train; do
  contains "Content-Signal states $sig explicitly" "$sig=" "$robots"
done
contains "robots.txt names the sitemap" "sitemap:" "$robots"
expect "sitemap.xml is served" 200 "$(status "$BASE/sitemap.xml")"

echo; echo "4. Link headers and 404s"
link="$(header link "$BASE/")"
contains "home page Link: alternate markdown" 'text/markdown' "$link"
if [ "$(status "$BASE/.well-known/api-catalog")" = 200 ]; then
  contains "home page Link: api-catalog" 'rel="api-catalog"' "$link"
  contains "api-catalog is a linkset" "linkset" "$(ctype "$BASE/.well-known/api-catalog")"
fi
expect "unknown page is a real 404" 404 "$(status "$BASE/some-path-that-does-not-exist-xyz")"
contains "HTML 404 points at llms.txt" "/llms.txt" "$(curl -sS "$BASE/some-path-that-does-not-exist-xyz")"
if [ -n "$API_404" ]; then
  expect "$API_404 is 404" 404 "$(status "$BASE$API_404")"
  expect "$API_404 answers in JSON" "application/json" "$(ctype "$BASE$API_404")"
  contains "$API_404 body has an error code" '"error"' "$(curl -sS "$BASE$API_404")"
fi

if [ -n "$MCP_CARD" ]; then
  echo; echo "5. MCP"
  expect "server card is served" 200 "$(status "$BASE$MCP_CARD")"
  card="$(curl -sS "$BASE$MCP_CARD")"
  contains "server card names a transport endpoint" '"endpoint"' "$card"
  contains "server card names serverInfo" '"serverInfo"' "$card"
  if [ -n "$MCP_ENDPOINT" ] && command -v npx >/dev/null 2>&1; then
    tools="$(npx -y @modelcontextprotocol/inspector --cli "$BASE$MCP_ENDPOINT" --transport http --method tools/list 2>/dev/null)"
    contains "MCP endpoint answers tools/list" '"tools"' "$tools"
  fi
fi

echo; printf '%s passed, %s failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
