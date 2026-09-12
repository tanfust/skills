---
name: paddle-webhooks
description: Build and verify the Paddle Billing webhook that fulfils one-time digital purchases into Supabase, with signature verification on the raw body, an event_id idempotency ledger, licences keyed on (transaction, product), download tokens, and refund and chargeback revocation driven by adjustment action and status with an occurred_at guard. Use this whenever the work touches Paddle webhooks or notification destinations, transaction.completed, adjustment.created or adjustment.updated, Paddle-Signature or pdl_ntfset_ secrets, paddle.webhooks.unmarshal, custom_data or supabase_user_id on a checkout, licence tables written from Paddle, duplicate fulfilment emails, a refund that did not revoke access, the Paddle simulator, or "invalid signature" and timeouts in the notifications log. Reach for it even for "just handle the webhook", because the failures charge or refund real people and nothing throws. Not for subscriptions (revenuecat-supabase-entitlements), domain approval (paddle-domain-verification), or Stripe.
license: MIT
---

# Paddle webhooks and fulfilment on Supabase

None of the bad outcomes here produce an error. A redelivered `transaction.completed` mints a second licence and sends a second email. A refund arrives as `adjustment.created` with `status: pending_approval`, the handler revokes, Paddle rejects the refund a day later, and the customer who kept paying has no access. A `chargeback_reverse` lands before the `chargeback` it reverses and the late one wins. The browser's `checkout.completed` event grants access to someone who closed the overlay before the charge settled. Paddle documents the primitives (at-least-once, no ordering, five-second deadline, `event_id`, `occurred_at`) and leaves the state machine to you. This skill is that state machine, extracted from a shipped store, with the checks that prove it holds.

Scope: one-time purchases of digital goods (licence plus gated download), Paddle Billing, Next.js route handlers, Supabase Postgres written with the service role. Every Paddle fact is quoted with its source in `references/EVENTS.md`; the tables and handler are in `references/SCHEMA.md`.

## Order of work

1. Draw the trust boundary before writing a route
2. Create the notification destination
3. Write the route: raw body, verify, respond fast
4. Write the ledger and the licence constraint
5. Fulfil `transaction.completed`
6. Apply adjustments by action and status
7. Verify with the simulator, the ledger and a real sandbox refund

## 1. Draw the trust boundary

Money and identity never come from the browser. The server mints the checkout: it reads the session with `getUser()`, maps the product to the Paddle price id for the active environment, and sets `customData` to `{ supabase_user_id, product_key }`. The browser only opens the overlay with what it was given. The webhook then re-derives what was bought from the charged `items[].price.id`, and treats `custom_data.product_key` as a fallback plus an alarm: if the charged price is not in this deployment's catalog, that is sandbox and production price ids drifting apart, and it must be logged loudly rather than fulfilled quietly.

Access is granted only from the verified webhook. The client's `checkout.completed` callback drives a "finalizing" spinner and nothing else. This is also why login is required to buy: with a real `user_id` in every event there is no unclaimed-order reconciliation to build.

## 2. Create the notification destination

Dashboard, Developer tools, Notifications. Subscribe to `transaction.completed`, `transaction.payment_failed`, `adjustment.created`, `adjustment.updated`, `customer.created`, `customer.updated`. Copy the `pdl_ntfset_` secret into a server-only variable. Sandbox and production are separate accounts with separate destinations, secrets, catalogs and price ids; keep one `.env` per environment and select the catalog by `NEXT_PUBLIC_PADDLE_ENV`.

For local work, expose the route through a tunnel and point a sandbox destination at it. Set `traffic_source` to `all` if you want both the simulator and real sandbox checkouts to hit it.

## 3. Write the route

Three rules, each from a documented constraint.

**Read the raw body.** The signature is HMAC-SHA256 over `ts:rawBody`; `request.json()` re-serialises and the bytes no longer match. Use `request.text()` and hand it to `paddle.webhooks.unmarshal(rawBody, secret, header)`, which verifies (five-second timestamp tolerance by default) and parses. A failed verification returns 400 and writes nothing.

**Keep the route out of middleware.** No session refresh, no bot detection, no CSRF on this path. It is a server-to-server POST with no cookies; a bot check rejects Paddle and the notifications log fills with 403s nobody reads.

**Return 200 within five seconds.** Paddle retries anything slower, and in sandbox it retries only three times within fifteen minutes. If your fulfilment does a database round trip, a token insert and an email send inside the request, measure it; the shipped handler stays under the deadline on a warm serverless function but a cold start plus a slow email provider does not. If you cannot stay under, insert the ledger row, return 200, and process from a queue or a follow-up job, which is what Paddle recommends.

## 4. Write the ledger and the licence constraint

Two constraints do the idempotency; code does not.

`paddle.webhook_events(event_id primary key)`: insert first, before any side effect. A unique violation (SQLSTATE `23505`) means this event was already handled; return 200 and do nothing. Store the payload so support can answer "what did Paddle send" without the Paddle dashboard.

`paddle.licenses unique (paddle_transaction_id, product_key)`: the upsert with `ignoreDuplicates` returns no row on a repeat, and no row means no second download token and no second email. This holds even if the ledger insert and the licence insert are not in one transaction, because a repeat of either step is a no-op on its own.

Store `last_event_at` on the licence, set from the event's `occurred_at`, never from arrival time. It is the only defence against out-of-order delivery.

## 5. Fulfil `transaction.completed`

Fulfil on `completed`, not `paid`. Completed is the last event for the purchase and carries settled totals; handling both gives you two events to reconcile. Resolve `user_id` from `custom_data.supabase_user_id`, resolve the product from the charged price id, upsert the licence, mint an expiring re-issuable download token, send the access email, mirror the transaction row for the account page.

Email is best effort. If the send throws and the handler returns 500, Paddle redelivers, the licence upsert returns nothing, and the email is never sent. So catch and log the send, and keep the account page able to re-issue a link from the licence, which it can because the licence, not the token, is the entitlement.

`transaction.payment_failed` charged nothing. Notify the buyer with the `payments[].error_code` and a retry link; issue nothing.

## 6. Apply adjustments by action and status

Do not revoke on `adjustment.created`. Read the table in `references/EVENTS.md` and apply the transition it names: `refund` revokes only at `status = approved` (most live refunds are created `pending_approval` and may be `rejected`); `chargeback` revokes; `chargeback_reverse` restores; `chargeback_warning` and `credit` are recorded and, for the warning, alert a person. Every update carries `.lte("last_event_at", occurred_at)` so a stale event cannot undo a newer state, and `.neq("status", next)` so the `created` and `updated` events for the same approval are one transition and one email.

Revocation stops future signed URLs; bytes already downloaded are gone. That is the Merchant of Record posture and the refund policy should say so.

## Failure modes worth recognizing quickly

| Symptom | Cause |
| --- | --- |
| `invalid signature` on every delivery, works with curl | Body parsed before verification, a proxy rewrote whitespace, or the secret is from the other environment |
| Notifications log shows retries with `timeout` | Handler over five seconds. Cold start plus email send is the usual pair |
| Two access emails, one licence | Ledger insert happened after the email, or the email is sent outside the `if (!created) return` guard |
| Two licences for one purchase | Missing `unique (paddle_transaction_id, product_key)`, or the upsert lacks `ignoreDuplicates` |
| Customer refunded, still has access | Handler listens to `adjustment.created` only and the refund was `pending_approval` then approved via `adjustment.updated`, which was not subscribed |
| Customer not refunded, lost access | Handler revoked on `pending_approval`; Paddle rejected the refund |
| Access lost after a dispute the seller won | `chargeback_reverse` treated as a chargeback because the code matched on the substring |
| Access restored, then lost again with no new event | `chargeback_reverse` arrived before `chargeback`; no `occurred_at` guard |
| Fulfilled in production, wrong product | Price id from the sandbox catalog resolved via the `custom_data.product_key` fallback; the anomaly log line was not read |
| Works in sandbox, first live purchase does nothing | Live destination not created, or subscribed to fewer events, or route blocked by middleware only in production |
| Sandbox test worked yesterday, not today, no log entry | Handler was down; sandbox retries three times in fifteen minutes, then marks the notification failed |

## 7. Verify

Four checks, in order. Run them in sandbox against the deployed handler, not a mock.

**Signature and no-write.** Send a request with the right shape and a wrong signature; expect 400 and an unchanged ledger.

```bash
BEFORE=$(psql "$DB" -tAc "select count(*) from paddle.webhook_events")
curl -s -o /dev/null -w '%{http_code}\n' -X POST "$SITE/api/paddle/webhook" \
  -H 'Paddle-Signature: ts=1;h1=deadbeef' -H 'Content-Type: application/json' -d '{"event_id":"evt_forged"}'
psql "$DB" -tAc "select count(*) - $BEFORE from paddle.webhook_events"
```

Pass: `400` and `0`.

**Idempotency.** In Developer tools, Simulations, create a single-event simulation of `transaction.completed` against your destination with `custom_data` set to a real test user and a mapped price id. Run it, then replay the same simulation so the same `event_id` is delivered again. Then:

```sql
select
  (select count(*) from paddle.webhook_events where event_id = :'evt') as ledger_rows,      -- 1
  (select count(*) from paddle.licenses where paddle_transaction_id = :'txn') as licenses,  -- 1
  (select count(*) from paddle.download_tokens t join paddle.licenses l on l.id = t.license_id
     where l.paddle_transaction_id = :'txn') as tokens;                                     -- 1
```

Pass: `1, 1, 1`, and exactly one access email in the mail log. Two of anything is a finding.

**Adjustment state machine.** Make a real sandbox purchase with a test card, then refund it from Transactions in the dashboard. Watch the licence: it must stay `active` while the adjustment is `pending_approval` and become `refunded` only when an event reports the refund `approved`; watch the notifications log for the `adjustment.updated` that carries it. Then send an edited single-event simulation of `adjustment.created` with `action: chargeback_reverse` and an `occurred_at` earlier than the refund's; the licence must not change. Query:

```sql
select status, revoked_reason, last_event_at from paddle.licenses where paddle_transaction_id = :'txn';
```

Pass: `refunded`, `refund`, and `last_event_at` equal to the approval's `occurred_at`, unchanged after the stale reversal. Confirm `/library/access/<token>` for that licence now redirects to the error page rather than a signed URL.

**Deadline.** In Developer tools, Notifications, open the last ten deliveries to the destination. Pass: every one `200`, none with a retry attempt, and the slowest response time under five seconds. A single timeout in the list is a finding even if the retry succeeded, because sandbox will not retry forever and production will retry for three days into a handler that is still slow.

Report as a table of `check / expected / observed / evidence`, with event ids, transaction ids and the notification ids from the dashboard as evidence. If all four pass, say so and name the destination URL, the environment, and the date, so the next person knows which deployment was proven.

## Where this stops

This skill covers one-time purchases: licence, token, revocation. It does not cover recurring billing, seat counts, proration, or entitlement state for subscriptions; the shape is similar but the event set (`subscription.*`) and the state machine are larger. It does not cover checkout UI beyond the server-minted `customData`, catalog management, tax, or Paddle's domain approval, which is `paddle-domain-verification`. Store the licence in the tenant boundary defined by `supabase-multi-tenant-rls` if the product is team-scoped rather than user-scoped.
