# Schema and handler shape

The tables the procedure in SKILL.md writes to, and the handler skeleton, as shipped. Adapt names; keep the constraints, because the constraints are the idempotency.

- [Tables](#tables)
- [Grants and RLS](#grants-and-rls)
- [Route](#route)
- [Processor](#processor)
- [Checkout preparation](#checkout-preparation)

## Tables

Live in a dedicated `paddle` schema so the Data API exposure is a deliberate choice per table.

```sql
create schema if not exists paddle;

-- Idempotency ledger. Primary key on event_id is the dedupe; the payload is the audit trail.
create table paddle.webhook_events (
  event_id     text primary key,               -- evt_... (ntfsimevt_... from the simulator)
  event_type   text not null,
  occurred_at  timestamptz not null,
  payload      jsonb not null,
  status       text not null default 'received', -- received | processed | failed
  error        text,
  processed_at timestamptz,
  received_at  timestamptz not null default now()
);

-- One entitlement per (transaction, product). The unique constraint is what makes a
-- redelivered transaction.completed a no-op even if the ledger row were lost.
create table paddle.licenses (
  id                    uuid primary key default gen_random_uuid(),
  license_key           text unique not null,
  user_id               uuid not null references auth.users(id) on delete cascade,
  product_key           text not null,          -- "<category>:<id>", unique across the catalog
  paddle_transaction_id text not null,
  status                text not null default 'active', -- active | refunded | disputed
  revoked_reason        text,                   -- the adjustment action that moved it
  last_event_at         timestamptz not null,   -- occurred_at of the last event applied
  created_at            timestamptz not null default now(),
  unique (paddle_transaction_id, product_key)
);
create index on paddle.licenses (user_id);
create index on paddle.licenses (product_key);

-- Bearer links for the fulfilment email. Expiring, re-issuable, never the licence itself.
create table paddle.download_tokens (
  token       text primary key,
  license_id  uuid not null references paddle.licenses(id) on delete cascade,
  expires_at  timestamptz not null,
  created_at  timestamptz not null default now()
);
create index on paddle.download_tokens (license_id);

-- Mirrors of Paddle entities, best effort, for the account page and support.
create table paddle.customers (
  id          text primary key,                 -- ctm_...
  email       text,
  name        text,
  status      text,
  custom_data jsonb not null default '{}',
  updated_at  timestamptz not null default now()
);
create table paddle.transactions (
  id              text primary key,             -- txn_...
  customer_id     text references paddle.customers(id) on delete set null,
  subscription_id text,
  status          text,
  currency_code   text,
  total           text,                          -- minor units, as Paddle sends it
  custom_data     jsonb not null default '{}'
);
```

## Grants and RLS

The webhook writes with the service role. Buyers read their own licences. Nothing else is reachable.

```sql
grant usage on schema paddle to service_role, authenticated;
grant all on all tables in schema paddle to service_role;
grant select on paddle.licenses to authenticated;

alter table paddle.webhook_events  enable row level security;  -- no policies: service role only
alter table paddle.download_tokens enable row level security;  -- no policies: service role only
alter table paddle.customers       enable row level security;
alter table paddle.transactions    enable row level security;
alter table paddle.licenses        enable row level security;

create policy "buyers read own licenses"
  on paddle.licenses for select to authenticated
  using (user_id = (select auth.uid()));
```

Run the `supabase-multi-tenant-rls` audit against the `paddle` schema too; the "tables with RLS enabled but no policies" query will list the two ledger tables, and that is the intended result.

## Route

```ts
// app/api/paddle/webhook/route.ts   (Next.js App Router; Node runtime, the SDK needs Node crypto)
import { getPaddle } from "@/lib/paddle/get-paddle-instance";
import { processWebhook } from "@/lib/paddle/process-webhook";

export async function POST(request: Request) {
  const secret = process.env.PADDLE_NOTIFICATION_WEBHOOK_SECRET;
  if (!secret) return new Response("not configured", { status: 500 });

  const signature = request.headers.get("paddle-signature") ?? "";
  const rawBody = await request.text();                 // never request.json(): parsing changes the bytes

  let event;
  try {
    event = await getPaddle().webhooks.unmarshal(rawBody, secret, signature);
  } catch {
    return new Response("invalid signature", { status: 400 });   // 4xx: Paddle does not retry a rejected signature usefully
  }
  if (!event) return new Response("invalid event", { status: 400 });

  try {
    await processWebhook(event);
    return new Response("ok", { status: 200 });
  } catch (error) {
    console.error("[paddle] processing failed", error);
    return new Response("processing error", { status: 500 }); // 5xx: retry. The ledger makes retries safe.
  }
}
```

Exclude this path from any middleware or proxy that touches cookies, sessions or bot detection. It is a server-to-server call with no browser attached; a bot check on it rejects Paddle.

## Processor

```ts
export async function processWebhook(event: EventEntity) {
  const db = createAdminClient();                       // service role, server only

  // 1. Ledger first. First writer wins; a duplicate delivery returns here.
  const { error } = await db.schema("paddle").from("webhook_events").insert({
    event_id: event.eventId, event_type: event.eventType,
    occurred_at: event.occurredAt, payload: event as unknown as Record<string, unknown>,
  });
  if (error) { if (error.code === "23505") return; throw error; }   // unique_violation

  try {
    switch (event.eventType) {
      case EventName.TransactionCompleted:     await fulfil(db, event.data, event.occurredAt); break;
      case EventName.AdjustmentCreated:
      case EventName.AdjustmentUpdated:        await applyAdjustment(db, event.data, event.occurredAt); break;
      case EventName.TransactionPaymentFailed: await notifyPaymentFailed(db, event.data); break;
      case EventName.CustomerCreated:
      case EventName.CustomerUpdated:          await upsertCustomer(db, event.data); break;
      default: break;                                   // recorded, not acted on
    }
    await db.schema("paddle").from("webhook_events")
      .update({ status: "processed", processed_at: new Date().toISOString() }).eq("event_id", event.eventId);
  } catch (e) {
    await db.schema("paddle").from("webhook_events")
      .update({ status: "failed", error: String(e) }).eq("event_id", event.eventId);
    throw e;
  }
}
```

Fulfilment, the part that must be exactly-once:

```ts
async function fulfil(db, txn: TransactionNotification, occurredAt: string) {
  const custom = (txn.customData ?? {}) as Record<string, unknown>;
  const userId = typeof custom.supabase_user_id === "string" ? custom.supabase_user_id : null;

  // The charged price is the authority for what was bought; custom_data is a fallback and an alarm.
  const chargedPriceId = txn.items?.[0]?.price?.id ?? txn.details?.lineItems?.[0]?.priceId ?? null;
  const productKey = (chargedPriceId ? productKeyForPriceId(chargedPriceId) : undefined)
                  ?? (typeof custom.product_key === "string" ? custom.product_key : undefined);
  if (!userId || !productKey) return;                   // not a fulfillable one-time purchase
  if (chargedPriceId && !productKeyForPriceId(chargedPriceId)) {
    console.error(`[paddle] price ${chargedPriceId} not mapped in ${process.env.NEXT_PUBLIC_PADDLE_ENV}; fulfilled from custom_data`);
  }

  const { data: created, error } = await db.schema("paddle").from("licenses")
    .upsert({ license_key: generateLicenseKey(), user_id: userId, product_key: productKey,
              paddle_transaction_id: txn.id, status: "active", last_event_at: occurredAt },
            { onConflict: "paddle_transaction_id,product_key", ignoreDuplicates: true })
    .select("id, license_key").maybeSingle();
  if (error) throw error;
  if (!created) return;                                 // already fulfilled: no second token, no second email

  const token = generateDownloadToken();
  await db.schema("paddle").from("download_tokens")
    .insert({ token, license_id: created.id, expires_at: new Date(Date.now() + 30 * 864e5).toISOString() });

  await trySend(() => sendAccessEmail(...));            // best effort: an email failure must not 500 the webhook
}
```

Adjustments, following the table in `EVENTS.md`:

```ts
async function applyAdjustment(db, adj: AdjustmentNotification, occurredAt: string) {
  const action = String(adj.action); const status = String(adj.status);
  let next: "refunded" | "disputed" | "active" | null = null;
  if (action === "refund" && status === "approved") next = "refunded";
  else if (action === "chargeback") next = "disputed";
  else if (action === "chargeback_reverse") next = "active";
  else return;                                          // pending_approval, rejected, warning, credit: recorded only

  const { data: changed } = await db.schema("paddle").from("licenses")
    .update({ status: next, revoked_reason: next === "active" ? null : action, last_event_at: occurredAt })
    .eq("paddle_transaction_id", adj.transactionId)
    .lte("last_event_at", occurredAt)                   // out-of-order guard
    .neq("status", next)                                // idempotent: created then updated for the same refund is one transition
    .select("user_id, product_key");
  if (!changed?.length) return;
  // notify per licence, best effort
}
```

## Checkout preparation

The server action that makes the webhook trustworthy. The browser receives a price id it cannot change the meaning of and a `customData` it did not write.

```ts
"use server";
export async function prepareCheckout(category: ProductCategory, id: string) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();   // getUser(), never getSession(), for authz
  if (!user) return { ok: false, error: "auth_required" };
  const productKey = `${category}:${id}`;
  const priceId = resolvePriceId(productKey);                  // per NEXT_PUBLIC_PADDLE_ENV
  if (!priceId) return { ok: false, error: "not_purchasable" };
  const { data: owned } = await supabase.schema("paddle").from("licenses")
    .select("id").eq("product_key", productKey).eq("status", "active").limit(1);
  if (owned?.length) return { ok: false, error: "already_owned" };
  return { ok: true, priceId, customData: { supabase_user_id: user.id, product_key: productKey }, customerEmail: user.email ?? "" };
}
```

The client then calls `paddle.Checkout.open({ items: [{ priceId, quantity: 1 }], customData, customer: { email }, settings: { successUrl } })` and nothing else. The `checkout.completed` browser event is a UI signal for a "finalizing" state; it grants nothing.
