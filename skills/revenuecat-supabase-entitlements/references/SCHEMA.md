# Table, function, identity and paywall states

The shipped shape, generalised. Keep the primary key and the RLS; rename the rest.

- [Table](#table)
- [Gating a content table](#gating-a-content-table)
- [Edge function](#edge-function)
- [Client identity](#client-identity)
- [Paywall states](#paywall-states)

## Table

```sql
-- Server-side mirror of RevenueCat entitlement state. Written only by the webhook
-- function with the service role. The client gates UI on the SDK; this table is
-- what RLS policies read, because a patched client can fake a paywall and cannot
-- fake a Postgres policy.
create table public.entitlements (
  user_id            uuid not null references auth.users(id) on delete cascade,
  entitlement_id     text not null,                 -- 'pro'
  is_active          boolean not null default false,
  expires_at         timestamptz,                   -- null for lifetime
  grace_period_ends  timestamptz,
  product_id         text,
  store              text,                          -- APP_STORE | PLAY_STORE | ...
  environment        text not null default 'PRODUCTION',  -- SANDBOX | PRODUCTION
  last_event_id      text,
  last_event_at      timestamptz,
  synced_at          timestamptz not null default now(),
  primary key (user_id, entitlement_id)
);

-- Idempotency ledger. RevenueCat retries and the dashboard has a Retry button.
create table public.revenuecat_events (
  id           text primary key,                    -- event.id
  type         text not null,
  app_user_id  text,
  event_at     timestamptz,
  payload      jsonb not null,
  status       text not null default 'received',    -- received | processed | failed | skipped
  error        text,
  received_at  timestamptz not null default now()
);

alter table public.entitlements       enable row level security;
alter table public.revenuecat_events  enable row level security;   -- no policies: service role only
grant select on public.entitlements to authenticated;
grant all on public.entitlements, public.revenuecat_events to service_role;

create policy "users read own entitlements"
  on public.entitlements for select to authenticated
  using (user_id = (select auth.uid()));
```

`environment` matters. Sandbox purchases from TestFlight or an internal-testing track arrive at the same webhook with `environment: SANDBOX`. Without the column, a tester's sandbox subscription unlocks production content, and a tester's sandbox expiration can overwrite a real one if the ids collide. Store it, and let the gating policy decide whether sandbox rows count.

## Gating a content table

The reason the table exists.

```sql
create policy "pro members read premium rows"
  on public.premium_articles for select to authenticated
  using (
    exists (
      select 1 from public.entitlements e
      where e.user_id = (select auth.uid())
        and e.entitlement_id = 'pro'
        and e.is_active
        and coalesce(e.grace_period_ends, e.expires_at, 'infinity') > now()
        and e.environment = current_setting('app.rc_environment', true)  -- 'PRODUCTION' in prod
    )
  );
```

Index `entitlements (user_id, entitlement_id)` is the primary key already, so the subquery is a point lookup. Follow `supabase-multi-tenant-rls` for the rest of the policy hygiene; this is the same shape as an `is_org_member` check.

## Edge function

Deployed with `supabase functions deploy revenuecat-webhook --no-verify-jwt`, because RevenueCat cannot present a Supabase JWT. The function does its own authentication.

```ts
import { createClient } from "npm:@supabase/supabase-js@2";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function secureEquals(a: string, b: string) {          // plain === leaks timing
  const x = new TextEncoder().encode(a), y = new TextEncoder().encode(b);
  if (x.length !== y.length) return false;
  let d = 0; for (let i = 0; i < x.length; i++) d |= x[i] ^ y[i]; return d === 0;
}

Deno.serve(async (req) => {
  const secret = Deno.env.get("REVENUECAT_WEBHOOK_SECRET") ?? "";
  if (!secret || !secureEquals(req.headers.get("Authorization") ?? "", secret)) {
    return new Response("unauthorized", { status: 401 });
  }
  // If HMAC signing is enabled in the dashboard, also verify X-RevenueCat-Webhook-Signature
  // (t=<ts>,v1=<hex>; HMAC-SHA256 over `${t}.${rawBody}`) before parsing.

  const { event } = await req.json();
  if (!event?.id) return new Response("no event", { status: 400 });

  const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);

  // 1. Ledger first. A duplicate id is a 200 and nothing else.
  const { error: led } = await db.from("revenuecat_events").insert({
    id: event.id, type: event.type, app_user_id: event.app_user_id,
    event_at: event.event_timestamp_ms ? new Date(event.event_timestamp_ms).toISOString() : null,
    payload: event,
  });
  if (led) { if (led.code === "23505") return ok({ duplicate: true }); return fail(led); }

  // 2. Which users need a refresh. TRANSFER names two; everything else names one.
  const ids = event.type === "TRANSFER"
    ? [...(event.transferred_from ?? []), ...(event.transferred_to ?? [])]
    : [event.app_user_id];
  const users = ids.filter((id: string) => UUID.test(id));   // $RCAnonymousID:... cannot map to auth.users
  if (users.length === 0) { await mark(db, event.id, "skipped"); return ok({ skipped: "no mappable user" }); }

  // 3. Read the truth from RevenueCat and write it. The event type is not consulted.
  try {
    for (const userId of users) await syncUser(db, userId, event);
    await mark(db, event.id, "processed");
    return ok({ synced: users.length });
  } catch (e) {
    await mark(db, event.id, "failed", String(e));
    return new Response("processing error", { status: 500 });   // RevenueCat retries, ledger makes it safe
  }
});

async function syncUser(db, userId: string, event) {
  const res = await fetch(`https://api.revenuecat.com/v1/subscribers/${encodeURIComponent(userId)}`, {
    headers: { Authorization: `Bearer ${Deno.env.get("REVENUECAT_SECRET_API_KEY")}` },
  });
  if (!res.ok) throw new Error(`subscribers ${res.status}`);
  const { subscriber } = await res.json();
  const now = Date.now();
  const rows = Object.entries(subscriber.entitlements ?? {}).map(([entitlementId, e]: [string, any]) => {
    const expires = e.expires_date ? Date.parse(e.expires_date) : null;
    const grace = e.grace_period_expires_date ? Date.parse(e.grace_period_expires_date) : null;
    const sub = subscriber.subscriptions?.[e.product_identifier];
    return {
      user_id: userId, entitlement_id: entitlementId,
      is_active: expires === null || expires > now || (grace !== null && grace > now),
      expires_at: expires ? new Date(expires).toISOString() : null,
      grace_period_ends: grace ? new Date(grace).toISOString() : null,
      product_id: e.product_identifier, store: sub?.store ?? event.store ?? null,
      environment: sub?.is_sandbox ? "SANDBOX" : "PRODUCTION",
      last_event_id: event.id, last_event_at: new Date(event.event_timestamp_ms).toISOString(),
      synced_at: new Date().toISOString(),
    };
  });
  // Entitlements the user no longer has at all do not appear in the response; deactivate them.
  await db.from("entitlements").update({ is_active: false, synced_at: new Date().toISOString() })
    .eq("user_id", userId).not("entitlement_id", "in", `(${rows.map(r => `"${r.entitlement_id}"`).join(",") || '""'})`);
  if (rows.length) { const { error } = await db.from("entitlements").upsert(rows, { onConflict: "user_id,entitlement_id" }); if (error) throw error; }
}
```

Because every write is a full read of current state, the order in which events arrive no longer matters: whichever runs last writes the same truth. `last_event_id` is kept for support, not for ordering.

## Client identity

The whole mapping depends on `app_user_id` being the Supabase user id.

- Configure the SDK with `appUserID = <supabase auth uid>` when a session exists, and call `Purchases.logIn(uid)` on sign-in and `Purchases.logOut()` on sign-out.
- A purchase made before sign-in belongs to an anonymous `$RCAnonymousID:` id. The webhook cannot map it, so acknowledge those events with `200` and a `skipped` status rather than a 4xx, or RevenueCat retries them for two and a half hours. When the user later signs in, `logIn` merges the anonymous id into the provided one (RevenueCat: "Anonymous ID and Provided ID have CustomerInfo merged"), and, depending on the project's transfer behaviour setting, purchases move between ids; the handler refreshes both sides of any `TRANSFER` so neither id is left stale.
- Do not put the RevenueCat customer on the profile row and look it up; the id is the uid, and the table is keyed on it.

## Paywall states

What the client has to render, from the SDK's `CustomerInfo`, with the server table as the authority for content access.

| State | Signal | What the UI shows |
| --- | --- | --- |
| Not configured | No API keys at build time | A setup note, not a broken paywall. The app must build and pass CI with zero credentials |
| Not entitled | `entitlements.active[id]` absent | Offerings from the current offering; a Restore button |
| Entitled, renewing | active, `willRenew` true | "Renews on <expirationDate>", Manage link (`managementURL`) |
| Entitled, cancelled | active, `willRenew` false | "Expires on <expirationDate>", Manage link. This is `CANCELLATION` on the server and access is still on |
| Billing issue, in grace | active, store shows billing retry | Access stays; a fix-payment nudge that deep-links to `managementURL` |
| Expired | not active, `latestExpirationDate` in the past | Back to offerings, wording that says "resubscribe" |
| Bought on another device or Apple ID | not active locally, receipt exists | Restore purchases; explain that restore uses the store account, not the app login |
| Signed out | anonymous app user id | Require sign-in before purchase, so the entitlement lands on a mappable id |

Feed the result of `purchase()` and `restorePurchases()` straight into state; do not wait for the listener round trip, which can take seconds and reads as a failed purchase.
