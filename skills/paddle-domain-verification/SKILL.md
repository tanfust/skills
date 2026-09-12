---
name: paddle-domain-verification
description: Get a product domain approved by Paddle's domain review on the first submission, or fix one that was rejected, by writing and checking the Terms and Conditions, Refund Policy and Privacy Policy plus the pricing page, navigation links and support details Paddle looks for when it acts as Merchant of Record. Use this whenever the work touches Paddle website approval or domain verification, a domain review rejection, "Refund policy contains qualifiers", "Legal entity on website doesn't match", Paddle legal pages, refund policy wording, money-back guarantee, terms of service or privacy policy for a site that sells through Paddle, adding a second product domain to a Paddle account, or paddle.net and Paddle Buyer Terms links. Reach for it even when the request is just "write me a refund policy", because the page is reviewed by a person and a rejected domain cannot take payments. Not for Paddle webhooks, checkout code, tax settings or Stripe.
license: MIT
---

# Paddle domain verification

Paddle reviews every domain you sell from before checkout will run on it. Most submissions are approved automatically; the rest go to a person, and a manual review takes five to seven business days per round. The rejection message names a category, not the sentence that caused it, so a policy page with one conditional clause costs a week, then another week if the fix guesses wrong. The pages themselves are twenty minutes of work. The skill is knowing what the reviewer is reading for, which Paddle spreads across four documents, and checking it before you submit rather than after.

Everything this skill asserts about Paddle is quoted with its source in `references/REQUIREMENTS.md`. When a line here and Paddle's current page disagree, Paddle's page wins; fix the skill.

## Order of work

1. Collect the facts that have to match
2. Make the site reviewable
3. Write the three pages
4. Link them and gate the purchase on them
5. Submit
6. Keep them in sync afterwards
7. Verify

## 1. Collect the facts that have to match

Ask for these before writing anything. Each one has caused a rejection when guessed.

- **Legal name, exactly as registered on the Paddle account.** Company name, or for a sole proprietor the person's legal name (Paddle: "legal name preferred for sole proprietors"). The terms must carry this name. A site that says "Acme Inc." while the Paddle account is a sole trader gets "Legal entity on website doesn't match the registered entity on your Paddle account".
- **Principal place of business and governing law.** State the country. Paddle does not require a jurisdiction clause, but a terms page without one reads as a template.
- **Support email and a phone number.** The handbook requires "buyer support details (email and phone number)" on the site. Put the email on a dedicated sending subdomain if transactional mail also goes from there; `supabase-auth-emails` covers why. The address must receive replies, so forwarding or inbound has to exist before the page goes live.
- **What is sold, and whether any of it is a service.** Paddle serves software. "Managed", "done for you", "we handle everything" and "consulting" tiers get "Paddle processes digital goods only" unless the page states the software does the work. Calling your own store a "marketplace" reads as the prohibited third-party marketplace; describe it as your catalogue of your products.
- **Refund window in days.** An exact integer, no conditions attached. Paddle recommends at least 30; its own policy already grants EU and UK buyers 14 by statute whatever your page says, so 14 is the floor and anything conditional is a rejection.
- **Data collected and third parties.** Only what the product actually does. Never list an analytics or auth vendor the site does not use; a privacy policy naming a tracker that is absent is a lie in the other direction and still a lie.

## 2. Make the site reviewable

The domain review page lists what the reviewer must be able to find: a clear description of the product, key features or deliverables, pricing or a pricing page (a screenshot is accepted if pricing is not live yet), the three legal documents reachable from navigation, HTTPS, and a live site. "Live" means not password-protected and not a holding page. If the product is pre-launch, ship a real landing page with real prices first; a review cannot pass against a coming-soon page.

## 3. Write the three pages

Templates are in `references/TEMPLATES.md`. They are starting points extracted from a live Paddle seller, with placeholders for the facts from step 1. Adapt them; do not publish placeholders.

**Terms and Conditions** must contain, in this order of importance:

1. The legal name from step 1, near the top, as the operator.
2. This sentence, verbatim, because the handbook requires it as written: "Our order process is conducted by our online reseller Paddle.com. Paddle.com is the Merchant of Record for all our orders. Paddle provides all customer service inquiries and handles returns."
3. A purchases section that says buyers purchase from Paddle, names "Paddle.com Market Limited and its affiliates (collectively, Paddle)", links <https://www.paddle.com/legal/buyer-terms>, states that prices exclude tax which Paddle calculates at checkout, and points refunds at your Refund Policy.
4. What the product is and what the licence permits and forbids.
5. Support email and phone.
6. Limitation of liability, governing law, contact. Standard clauses; the reviewer is not reading these, buyers and courts are.

**Refund Policy** is the page that gets rejected. Structure it so the window stands alone:

1. One paragraph stating the window: "You may request a full refund within N days of your purchase, for any reason." Nothing else in that paragraph. No "if", "unless", "except", "at our discretion", "may be eligible", "non-refundable", "processing fees".
2. How to request it: paddle.net, the email used at checkout, the order; and your support email as the alternative.
3. That Paddle issues the refund to the original payment method and how long it takes to appear (Paddle: 3 to 5 working days for cards, up to 48 hours for PayPal).
4. Anything else you need, such as licence revocation on refund or a request to contact you before a chargeback, in its own section further down. These are not conditions on the refund window, but a reviewer scanning the window paragraph must not find them there.

**Privacy Policy** must exist and be reachable; Paddle publishes no content requirement beyond that. Write it truthfully and it satisfies the review:

1. You as data controller for site and account data; Paddle as an independent controller for payment data, with a link to <https://www.paddle.com/legal/privacy>. That is how Paddle describes itself.
2. What Paddle collects at checkout and what you receive back from Paddle (order status, identifiers, billing email), so it is clear card data never reaches you.
3. The rest is ordinary: data collected, purposes, retention, third parties, rights, contact. GDPR and CCPA sections are for your EU and California buyers, not for Paddle.

Set a visible "Last updated" date on all three. Reviewers and buyers both look for it.

## 4. Link them and gate the purchase on them

All three pages go in the site footer or main navigation on every page, including the pricing page, not only in the checkout flow. The handbook also requires that the buyer "accepts their terms & conditions and refund policy before they make a purchase": a checkbox or an explicit "By purchasing you agree to the Terms and Refund Policy" line with links, on the page that opens checkout.

## 5. Submit

Dashboard, Checkout, Website approval. Submit the domain buyers will check out from; subdomains and secondary product domains are separate submissions. If the review asks for more information, answer the same day; "we've not received a response from you" is one of the three rejection reasons Paddle lists.

## 6. Keep them in sync afterwards

Two obligations outlast the approval. The handbook requires you to "notify us of any changes in your refund policy, product T&C or contact details", so a refund window change is a message to Paddle support, not just an edit. And the legal entity on the site must keep matching the Paddle account; incorporating later means updating the terms the same day you update the account.

## Failure modes worth recognizing quickly

The three rejection reasons Paddle publishes are broad. The quoted messages below come from Paddle's own pages where they exist and from a published seller report where they do not; `references/REQUIREMENTS.md` says which is which.

| Symptom | Cause |
| --- | --- |
| "Refund policy contains qualifiers. Please provide unconditional refund terms matching our standard policy." | A condition in the refund window paragraph: "if the product fails to", "processing fees may apply", "at our discretion", "except" |
| "Legal entity on website doesn't match the registered entity on your Paddle account." | Terms name a company or brand that differs from the Paddle account's registered name |
| "Paddle processes digital goods only." or an AUP rejection | Page copy sells services, consulting, a managed tier described as humans doing work, or describes the site as a marketplace for third parties |
| "Our team has requested more information about your website and we've not received a response" | The review email went to a mailbox nobody reads. Check the account email during the review window |
| Approved automatically, then problems at first refund or dispute | Pages were never checked because no human read them. Run step 7 anyway; auto-approval is not a review |
| Reviewer cannot find pricing | Prices only appear inside the app after sign-up. Put a public pricing page or screenshot on the domain |
| Second product domain rejected while the first passed | Each domain is reviewed on its own content; the new domain lacks its own three pages or its own pricing |
| Buyers email support and get nothing | Support address on the pages is on a subdomain with no inbound routing |

## 7. Verify

Two parts. The first is mechanical and runs before submission. The second is the actual pass and comes from Paddle.

**Static check of the live pages.** Run against the deployed domain, not localhost, because HTTPS and navigation are part of what is reviewed. Substitute the three page URLs, the legal name and the window.

```bash
SITE=https://example.com; LEGAL="Acme Ltd"; DAYS=30
for p in / /terms /refund /privacy /pricing; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -L "$SITE$p"); [ "$code" = 200 ] || echo "FAIL $p returned $code"
done
curl -sL "$SITE/" | grep -oiE 'href="[^"]*(terms|refund|privacy|pricing)[^"]*"' | sort -u | wc -l | xargs -I{} sh -c '[ {} -ge 4 ] || echo "FAIL home page links to fewer than 4 of terms/refund/privacy/pricing"'
T=$(curl -sL "$SITE/terms")
echo "$T" | grep -q "$LEGAL" || echo "FAIL terms: legal name not found"
echo "$T" | grep -q "Paddle.com is the Merchant of Record for all our orders" || echo "FAIL terms: verbatim Merchant of Record sentence missing"
echo "$T" | grep -q "paddle.com/legal/buyer-terms" || echo "FAIL terms: Buyer Terms link missing"
R=$(curl -sL "$SITE/refund")
echo "$R" | grep -qE "$DAYS[- ]day|within \**$DAYS\** days" || echo "FAIL refund: '$DAYS days' not stated"
echo "$R" | grep -q "paddle.net" || echo "FAIL refund: paddle.net not mentioned"
echo "$R" | grep -oiE '.{0,120}\b'"$DAYS"'\b.{0,160}' | grep -iE '\b(if|unless|except|discretion|eligible|non-refundable|processing fee|subject to)\b' && echo "FAIL refund: a condition sits next to the refund window"
P=$(curl -sL "$SITE/privacy")
echo "$P" | grep -qi "paddle" || echo "FAIL privacy: Paddle not mentioned"
echo "$P" | grep -qi "controller" || echo "FAIL privacy: controller relationship not stated"
```

Pass: nothing printed. Every line printed is a finding with the page and the missing item in it. The condition grep is a heuristic and may flag a benign sentence; read the match before deciding, but do not submit with an unread match.

Then two things the script cannot see: the support phone number is on the site, and the page that opens checkout shows terms and refund acceptance. Look at both in a browser and say where you saw them.

**The actual pass.** Submit, then read the domain's status in the dashboard under Checkout, Website approval. Pass is the status Approved. Anything else is not a pass, including "we usually get approved", including a green static check. If the status is rejected, paste the rejection text into the failure-modes table above to pick the fix, correct the page, re-run the static check, resubmit.

Report as a table of `check / page / result / evidence`, one row per script line and one per manual look, followed by one line giving the dashboard status and the date. If the static check is clean and the status is Approved, say so and list the legal name, refund window and the three URLs that were checked, so the next person can tell a verified approval from a remembered one.

## Where this stops

This skill gets a domain through Paddle's review and keeps it compliant with the seller handbook. It is not legal advice: the templates are a seller's working pages, not counsel, and the liability, governing law and consumer-rights sections need a lawyer's eye for your jurisdiction and your buyers'. It does not cover Paddle checkout integration, webhooks, fulfilment, tax configuration, or Stripe, whose review process is different.
