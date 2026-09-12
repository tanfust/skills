# Paddle delivery facts and the adjustment state machine

Quoted or closely paraphrased from Paddle's developer documentation, read 2026-09-12. Re-read before relying on a number.

- [Delivery guarantees](#delivery-guarantees)
- [Signature](#signature)
- [Retry schedule](#retry-schedule)
- [Simulator](#simulator)
- [custom_data](#custom_data)
- [transaction events](#transaction-events)
- [Adjustments: action and status](#adjustments-action-and-status)
- [What to do per adjustment event](#what-to-do-per-adjustment-event)

## Delivery guarantees

Source: <https://developer.paddle.com/webhooks/about/how-webhooks-work> and <https://developer.paddle.com/webhooks/respond-to-webhooks>

- At-least-once. "`event_id`: Unique ID for this event, prefixed with `evt_`. Use this to deduplicate events you may receive more than once."
- `notification_id` is "Unique ID for this delivery attempt, prefixed with `ntf_`. Different from `event_id` because a single event can produce multiple notifications."
- No ordering. "We can't guarantee the order of delivery for webhooks. They may be delivered in a different order to the order they're generated. Store and check the `occurred_at` date against a webhook before making changes."
- Deadline. You must "return `200` within five seconds of receiving a request". Paddle recommends you "respond before doing any internal processing" and "process webhooks asynchronously by queueing received events and processing them in order."
- Dedup advice, verbatim: "Using `event_id` as a deduplication key is the simplest approach: store it when you first process an event, and skip any event with an ID you've already seen."

## Signature

Source: <https://developer.paddle.com/webhooks/signature-verification>

- Header `Paddle-Signature`, format `ts=<unix seconds>;h1=<hex hmac>`. During secret rotation the header can carry more than one `h1`.
- Signed payload is `ts` + `:` + the raw request body. "Don't transform or process the raw body of the request, including adding whitespace or applying other formatting."
- HMAC-SHA256 with the notification destination's secret key, prefixed `pdl_ntfset_`.
- "The default tolerance between the timestamp and the current time is five seconds." That is the replay window.
- Node SDK helper: `paddle.webhooks.unmarshal(rawBody, secretKey, signature)`, which verifies and parses in one call and throws on a bad signature.

## Retry schedule

Source: <https://developer.paddle.com/webhooks/respond-to-webhooks>

- Sandbox: "3 times within 15 minutes".
- Live: "60 times within 3 days. The first 20 attempts happen in the first hour, with 47 in the first day", exponential backoff.
- "When all attempts to deliver a webhook are exhausted, its status is set to `failed`." Failed notifications can be redelivered with the replay-a-notification API operation or inspected under Developer Tools, Notifications.
- Paddle publishes source IP lists for sandbox and live on the same page if you allowlist.

The sandbox number is the one that bites: three attempts in fifteen minutes means a handler that is down for twenty minutes in sandbox loses the event, and the test that "worked yesterday" silently never fulfils today.

## Simulator

Source: <https://developer.paddle.com/webhooks/test-webhooks>

- Dashboard: Paddle, Developer tools, Simulations. Sends single events or scenarios to a notification destination whose `traffic_source` is `simulation` or `all`.
- Simulated events carry a real `Paddle-Signature` and IDs prefixed `ntfsimevt_`, so signature verification and the ledger can be exercised without a purchase.
- Single-event payloads can be edited (PATCH the simulation with a `payload` object), which is how you send the same `event_id` twice or set `occurred_at` in the past.

## custom_data

Source: <https://developer.paddle.com/build/transactions/custom-data>

- Set on checkouts via Paddle.js `customData`, on transactions and subscriptions via the API.
- Included on transaction events. "Where a transaction has custom data against it, that data is copied to the created subscription", and subscription custom data is copied to transactions created from it (renewals, changes, one-time charges).
- Paddle does not warn about it, so this does: anything set in the browser is attacker-controlled. Mint `custom_data` server-side and treat it as a hint the webhook re-validates, never as authority for identity or price.

## transaction events

Source: <https://developer.paddle.com/webhooks/transactions/transaction-completed>

- `transaction.paid` fires when payment is captured. `transaction.completed` fires after Paddle finishes processing: "Transactions move to completed after they're `paid`", once fees, earnings, invoice number and any subscription creation are done.
- `transaction.completed` carries `items[].price.id`, `details.line_items`, `details.totals`, `customer_id`, `subscription_id` when relevant, and `custom_data`.
- Fulfil on `transaction.completed`. It is the last event for the purchase and carries the settled amounts. Fulfilling on `paid` as well doubles your work and gives you two events to deduplicate against each other.
- `transaction.payment_failed` carries the failed attempt under `payments[]` with an `error_code`; nothing was charged.

## Adjustments: action and status

Source: <https://developer.paddle.com/webhooks/adjustments/adjustment-created>

"Adjustments are used to refund or credit all or part of a completed or billed transaction."

| `action` | Meaning, per Paddle |
| --- | --- |
| `refund` | "Refunds some or all the related transaction. Must be approved by Paddle in most cases." |
| `credit` | "Credits some or all the related transaction." |
| `chargeback` | "Automatically created by Paddle when a customer successfully disputes a charge." |
| `chargeback_warning` | "Warning of an upcoming chargeback for the related transaction." |
| `chargeback_reverse` | "Reversal of a chargeback for the related transaction." |
| `credit_reverse` | "Reversal of a credit for the related transaction." |

| `status` | Meaning, per Paddle |
| --- | --- |
| `pending_approval` | "Adjustment is pending approval by Paddle." Most live refunds start here |
| `approved` | "Default for credits. Set when Paddle approves a refund." |
| `rejected` | "Set when Paddle rejects a refund that was pending_approval." |
| `reversed` | "Set by Paddle when a reversal adjustment is created." |

`adjustment.updated` fires "when the status changes to approved or rejected". Each adjustment names its `transaction_id` and `customer_id`, and carries `totals` (subtotal, tax, total, fee, earnings) in minor units as strings.

## What to do per adjustment event

Derived from the two tables above. The mistake this prevents: revoking on `adjustment.created` regardless of `status`, which pulls access on a refund Paddle later rejects and never gives it back, and marks a `chargeback_warning` as a lost dispute.

| Event | `action` | `status` | Do |
| --- | --- | --- | --- |
| created or updated | `refund` | `approved` | Revoke: `status = refunded` |
| created | `refund` | `pending_approval` | Record only. Optionally flag the licence; do not revoke |
| updated | `refund` | `rejected` | Nothing to undo if you followed the row above; clear any flag |
| created | `credit` | `approved` | Business decision. A credit is money back without reversing the sale; most digital sellers leave access in place |
| created | `chargeback` | any | Revoke: `status = disputed` |
| created | `chargeback_warning` | any | Record and alert a human. Access stays |
| created | `chargeback_reverse` | any | Restore: `status = active` if the only reason it left `active` was the chargeback |
| created | `credit_reverse` | any | Mirror of your credit decision |
| any | partial amount (`totals.total` below the transaction total) | | Decide explicitly. For one licence per transaction, a partial refund usually keeps access; say so in the code |

Every transition is guarded by `occurred_at >= licenses.last_event_at`, so a `chargeback_reverse` that arrives before the `chargeback` it reverses cannot be undone by the late arrival.
