# RevenueCat webhook facts and what each event means for access

Quoted or closely paraphrased from RevenueCat's documentation, read 2026-09-12. Re-read before relying on a timing or an enum.

- [Delivery](#delivery)
- [Authentication](#authentication)
- [Payload](#payload)
- [Event types](#event-types)
- [Why the event type is not the access state](#why-the-event-type-is-not-the-access-state)
- [The fetch that is the source of truth](#the-fetch-that-is-the-source-of-truth)

## Delivery

Source: <https://www.revenuecat.com/docs/integrations/webhooks>

- Success is a `200`. "RevenueCat will retry later (up to 5 times) with an increasing delay (5, 10, 20, 40, and 80 minutes)." Five retries, so the last attempt is about two and a half hours after the first; after that the event is gone unless you replay it from the dashboard.
- "If your server doesn't finish the response in 60s, RevenueCat will disconnect."
- "Your application may receive a webhook for the same event more than once, and it is something your webhook processing should be prepared to handle." "We recommend you to guard against duplicated events by making your webhook processing idempotent. For example, you can keep track of the event `id`."
- No ordering guarantee is stated anywhere on the page. Treat arrival order as meaningless.
- "You can test your server side implementation by purchasing sandbox subscriptions or by issuing test webhook events through RevenueCat's dashboard."

## Authentication

Source: same page.

- Shared secret: "We recommended setting an authorization header value via the RevenueCat dashboard. When set, RevenueCat will send this header in every request." You choose the value; RevenueCat sends it verbatim as `Authorization`.
- HMAC, optional: "When enabled, every delivery includes an `X-RevenueCat-Webhook-Signature` header with the format: `t=<unix_timestamp>,v1=<hmac_sha256_hex>`". "The HMAC-SHA256 is computed over `"<timestamp>.<raw_json_body>"` using your integration's signing secret." "Optionally reject requests where `abs(now - t)` exceeds your tolerance (e.g. 5 minutes) to prevent replay attacks." "RevenueCat recomputes `t` and `v1` on every delivery attempt, including automatic retries and a manual `Retry` from the dashboard."
- RevenueCat cannot mint a Supabase JWT, so a Supabase Edge Function receiving these must be deployed with `--no-verify-jwt` and do its own check on the header above.

## Payload

Source: <https://www.revenuecat.com/docs/integrations/webhooks/sample-events> and <https://www.revenuecat.com/docs/integrations/webhooks/event-types-and-fields>

- Top level: `{ "api_version": "1.0", "event": { ... } }`.
- Identity: `app_user_id` is the "Last seen App User ID of the subscriber"; `original_app_user_id` "The first App User ID used by the subscriber"; `aliases` "All App User IDs ever used by the subscriber".
- `entitlement_ids` is an array (`["pro"]`); `entitlement_id` is deprecated.
- `id` is the "Unique identifier of the event"; `event_timestamp_ms` "The time that the event was generated".
- `expiration_at_ms`, `grace_period_expiration_at_ms`, `auto_resume_at_ms` (paused Play subscriptions), `purchased_at_ms`.
- `environment` is `SANDBOX` or `PRODUCTION`. `store` includes `APP_STORE`, `PLAY_STORE`, `AMAZON`, `STRIPE`, `PADDLE`, `RC_BILLING`, `ROKU`. `period_type` is `TRIAL`, `INTRO`, `NORMAL`, `PROMOTIONAL` or `PREPAID`.
- `cancel_reason` and `expiration_reason`: `UNSUBSCRIBE`, `BILLING_ERROR`, `DEVELOPER_INITIATED`, `PRICE_INCREASE`, `CUSTOMER_SUPPORT`, `UNKNOWN`; expiration also `SUBSCRIPTION_PAUSED`.
- `TRANSFER` events carry `transferred_from` and `transferred_to` arrays of app user ids and no `entitlement_ids`.

## Event types

Source: event-types-and-fields page, descriptions verbatim.

| Type | RevenueCat's description |
| --- | --- |
| `INITIAL_PURCHASE` | "A new subscription was purchased" |
| `RENEWAL` | "An existing subscription was renewed, or a lapsed user resubscribed" |
| `CANCELLATION` | "A subscription or non-renewing purchase was canceled or refunded" |
| `UNCANCELLATION` | "A non-expired canceled subscription was re-enabled" |
| `NON_RENEWING_PURCHASE` | "A customer has made a purchase that won't auto-renew" |
| `EXPIRATION` | "A subscription has expired" |
| `BILLING_ISSUE` | "An attempt to charge the subscriber failed" |
| `PRODUCT_CHANGE` | "A subscriber has changed the product of their subscription" |
| `SUBSCRIPTION_PAUSED` | "The subscription was scheduled to pause at the end of the current period" |
| `SUBSCRIPTION_EXTENDED` | "An existing subscription was extended" |
| `REFUND_REVERSED` | "A refund was reversed" |
| `TRANSFER` | "A transfer of transactions and entitlements was initiated between App User ID(s)" |
| `TEMPORARY_ENTITLEMENT_GRANT` | "RevenueCat issued a temporary outage grant to a customer" |
| `TEST` | "RevenueCat issued a test event" |
| `INVOICE_ISSUANCE`, `VIRTUAL_CURRENCY_TRANSACTION`, `EXPERIMENT_ENROLLMENT`, `PURCHASE_REDEEMED`, `PRICE_INCREASE_CONSENT_*` | Present in the list; not part of access state |

## Why the event type is not the access state

Reading the table above against the question "does this user have access right now":

- `CANCELLATION` means auto-renew was turned off **or** a refund happened. The first keeps access until `expiration_at_ms`; the second removes it now. The type alone cannot tell you which.
- `BILLING_ISSUE` starts a grace period. Access usually continues until `grace_period_expiration_at_ms`; turning it off at the event loses paying customers whose card retry succeeds.
- `SUBSCRIPTION_PAUSED` is "scheduled to pause at the end of the current period". Access continues until then.
- `TRANSFER` moves entitlements from one app user id to another and carries no `entitlement_ids`. A handler that keys on `entitlement_ids` skips it, and the old id keeps access in your table forever.
- `PRODUCT_CHANGE` may change which entitlements the subscription grants.
- Events arrive out of order and at most six times over two and a half hours, then never. A state machine built on the types has to be right about all of the above and still loses when a delivery is dropped.

This is why the vendor's own advice is the procedure: treat the event as a trigger, then read the current state.

## The fetch that is the source of truth

Source: <https://www.revenuecat.com/docs/integrations/webhooks> and <https://www.revenuecat.com/docs/api-v1/customers>

- "We recommend calling the `GET /subscribers` REST API endpoint after receiving any webhook."
- `GET https://api.revenuecat.com/v1/subscribers/{app_user_id}`, Bearer auth with a secret API key. The path is "Get or Create Customer": an unknown id is created, so only call it with ids you already know.
- Under `subscriber.entitlements.{entitlement_id}`: `expires_date` (null for lifetime), `grace_period_expires_date`, `product_identifier`, `purchase_date`.
- Under `subscriber.subscriptions.{product_id}`: `expires_date`, `billing_issues_detected_at`, `unsubscribe_detected_at`, `refunded_at`, `grace_period_expires_date`, `is_sandbox`, `store`, `period_type`.

Access for an entitlement is then one expression: `expires_date is null or expires_date > now()`, with `grace_period_expires_date` extending it when set. Write that, per entitlement, for the user named in the event, and for both sides of a `TRANSFER`. The event type becomes a log line.

API v2 exposes the same thing as a subscription `status` (`active`, `expired`, `in_grace_period`, `in_billing_retry`, `paused`, `incomplete`, `unknown`) and a `gives_access` boolean, with `Authorization: Bearer <v2 secret key>`. Either API works; do not mix the two in one handler.
