---
name: revenuecat-supabase-entitlements
description: Sync RevenueCat subscription state into a Supabase entitlements table so Row Level Security can gate premium content server-side, with an Edge Function webhook that checks the shared Authorization header, dedupes on event id, then fetches the customer from GET /v1/subscribers and writes expiry-based truth instead of guessing from the event type. Use this whenever the work touches RevenueCat webhooks, entitlements or CustomerInfo, app_user_id mapped to a Supabase auth uid, INITIAL_PURCHASE, RENEWAL, CANCELLATION, EXPIRATION, BILLING_ISSUE or TRANSFER events, purchases_flutter or react-native-purchases with Supabase, paywall states, premium rows hidden from non-subscribers, sandbox purchases unlocking production, or supabase functions deploy --no-verify-jwt. Reach for it even for "just store whether the user is pro", because the client can be patched and the event type lies about access. Not for one-time purchases through Paddle (paddle-webhooks) or web billing.
license: MIT
---

# RevenueCat entitlements in Supabase

The client already knows whether the user is subscribed; the SDK caches `CustomerInfo` and the paywall reads it instantly. The problem is that a client can be patched, and Postgres cannot ask the SDK. So a premium table needs an `entitlements` row it can join on, and that row is written by a webhook you own. The failures are all quiet: a `BILLING_ISSUE` handled as "revoke" cuts off a customer whose card retry succeeds tomorrow; a `CANCELLATION` handled as "keep until expiry" keeps access after a refund; a `TRANSFER` skipped because it carries no `entitlement_ids` leaves the old account subscribed forever; a TestFlight tester's sandbox purchase unlocks production rows. RevenueCat's own guidance avoids all of this with one move, and this skill is that move plus the checks.

Extracted from a shipped Flutter and Supabase codebase. Every RevenueCat fact is quoted with its source in `references/EVENTS.md`; the table, function and paywall states are in `references/SCHEMA.md`.

## Order of work

1. Make the app user id the Supabase uid
2. Create the table and the RLS that reads it
3. Deploy the webhook function without JWT verification and with its own auth
4. Treat the event as a trigger: dedupe, fetch, write
5. Keep sandbox out of production
6. Render the paywall from the SDK, gate content from the table
7. Verify

## 1. Make the app user id the Supabase uid

Everything downstream keys on `event.app_user_id` being a value that exists in `auth.users`. Configure the SDK with `appUserID = <auth uid>` when a session exists, call `logIn(uid)` on sign-in and `logOut()` on sign-out, and require sign-in before purchase. A purchase made anonymously lands on a `$RCAnonymousID:` id the webhook cannot map; acknowledge those events with `200` and log them as skipped rather than returning 4xx, or RevenueCat retries them for the next two and a half hours.

## 2. Create the table and the RLS that reads it

`public.entitlements (user_id, entitlement_id)` as the primary key, `is_active`, `expires_at`, `grace_period_ends`, `environment`, written only by the service role; authenticated users may select their own rows and nothing else. A content table's policy then joins on it: active, not expired (grace period included), and `environment = 'PRODUCTION'` in production. The primary key makes the join a point lookup, so it costs nothing per row. Schema and policy are in `references/SCHEMA.md`.

Keep a `revenuecat_events` ledger keyed on the event `id`. RevenueCat says plainly that the same event can arrive more than once and that the dashboard's Retry re-signs and re-sends.

## 3. Deploy the function with its own auth

RevenueCat cannot present a Supabase JWT, so the function is deployed with `supabase functions deploy revenuecat-webhook --no-verify-jwt` and authenticates the request itself. Set a long random value as the `Authorization` header in RevenueCat, Integrations, Webhooks, and the same value as a function secret; compare them with a constant-time comparison. If HMAC signing is enabled in the dashboard, also verify `X-RevenueCat-Webhook-Signature` (`t=<ts>,v1=<hex>`, HMAC-SHA256 over `<t>.<raw body>`) with a tolerance of a few minutes. Respond within 60 seconds; the fetch in the next step takes well under one.

## 4. Treat the event as a trigger

Insert the event id into the ledger first; a unique violation is a duplicate and returns `200` with no further work. Then, instead of mapping the event type to an access decision, do what RevenueCat recommends: call `GET /v1/subscribers/{app_user_id}` with the secret API key and write what it says. For each entitlement in the response, `is_active` is `expires_date is null or expires_date > now()`, extended by `grace_period_expires_date` when present. Entitlements missing from the response are deactivated. For a `TRANSFER`, run the same refresh for every id in `transferred_from` and `transferred_to`.

This makes ordering irrelevant. Two events for the same user arriving reversed both write the current truth, and a dropped delivery is repaired by the next event or by the reconciliation query in step 7. The event type is stored for support and never consulted for access. `references/EVENTS.md` lists, event by event, why the type on its own gets access wrong.

## 5. Keep sandbox out of production

Sandbox purchases from TestFlight and Play internal testing hit the same webhook URL with `environment: SANDBOX`, and the subscriber fetch marks them `is_sandbox`. Store the environment on the row and let the gating policy require `PRODUCTION`. Without it, every tester is a paying customer in your data and any content behind the policy is open to them.

## 6. Render the paywall from the SDK, gate content from the table

Two sources, two jobs. The SDK's `CustomerInfo` is instant and offline-cached, so the UI reads it: not configured, not entitled, entitled and renewing, entitled and cancelled with an expiry date, billing issue in grace, expired, restore needed on a new device, signed out. The table in the previous step is only for RLS. Feed the result of a purchase or restore straight into UI state; waiting for the listener round trip reads as a failed purchase. The full state table is in `references/SCHEMA.md`.

Every method in the purchase layer must degrade to a no-op when no API keys are configured, so the app builds, boots and passes CI with zero credentials and the paywall shows a setup note instead of an error.

## Failure modes worth recognizing quickly

| Symptom | Cause |
| --- | --- |
| Webhook returns `401` for every delivery | Function deployed with JWT verification on, or the dashboard header value differs from the function secret by whitespace |
| Customer paid, no row appears | `app_user_id` is anonymous because the purchase happened before sign-in, or the SDK was configured without `appUserID` |
| Access cut off on a failed card, restored payment did not bring it back | Handler set `is_active = false` on `BILLING_ISSUE` and nothing later set it true; use the fetch, which reads the grace period |
| Refunded user still has access | Handler treated `CANCELLATION` as "keep until expiry"; the fetch sees `refunded_at` and a past `expires_date` |
| Old account keeps access after the user signed in on a new one | `TRANSFER` skipped because it has no `entitlement_ids`; refresh `transferred_from` too |
| Testers see premium content in production | No `environment` column, or the policy ignores it |
| Row flips inactive then active for the same user within a minute | Event-type state machine plus out-of-order delivery; replace with the fetch |
| Same event processed twice, two analytics purchases | No ledger on `event.id` |
| Everything works in sandbox, first production customer gets nothing | Production API key not set as a function secret, or the webhook integration points at the sandbox project |

## 7. Verify

Run against a deployed function, with a real device or simulator signed in as a test user whose uid you know.

**Auth and duplicates.** Send a request without the header and expect `401`. Then, from RevenueCat, Integrations, Webhooks, send a test event; expect `200`, one `revenuecat_events` row with `type = 'TEST'`, and no change to `entitlements`. Press Retry on that same delivery and confirm the ledger still has one row for that id.

**Purchase to policy.** Make a sandbox purchase in the app. Within seconds:

```sql
select entitlement_id, is_active, expires_at, environment
from public.entitlements where user_id = :'uid';
```

Pass: one row, `is_active = true`, `expires_at` in the future, `environment = 'SANDBOX'`. Then, impersonating that user in a transaction (the recipe is in `supabase-multi-tenant-rls`, `references/AUDIT.md`), select from the gated table with the policy's environment set to `SANDBOX`: rows come back. Impersonate a second user: zero rows. Set the environment to `PRODUCTION`: zero rows for the tester as well.

**Expiry.** Sandbox subscriptions renew on an accelerated clock and stop after a few renewals. Leave the test subscription until `EXPIRATION` arrives (or cancel it in the store's sandbox settings) and re-run the query. Pass: `is_active = false`, the gated select returns nothing.

**Drift.** The reconciliation query, which should be run on a schedule as well as here:

```sql
select user_id, entitlement_id, expires_at, grace_period_ends
from public.entitlements
where is_active and coalesce(grace_period_ends, expires_at) < now() - interval '1 hour';
```

Pass: zero rows. Any row is an entitlement the webhook never turned off, and the fix is a fetch for that user, not a manual update.

Report as a table of `check / expected / observed / evidence`, with event ids from the RevenueCat webhook log and the test uid as evidence. If all four pass, say so and record the project, environment and date.

## Where this stops

This skill covers the sync from RevenueCat to Postgres and the policy that reads it. It does not cover configuring products and offerings in the stores, receipt validation (RevenueCat does that), pricing experiments, or web billing. One-time digital purchases through Paddle are `paddle-webhooks`; the tenant boundary a team plan would need is `supabase-multi-tenant-rls`.
