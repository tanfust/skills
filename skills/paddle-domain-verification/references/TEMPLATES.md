# Page templates

Three pages, extracted from a live Paddle seller's site and reduced to placeholders. Replace every `{{PLACEHOLDER}}` with the facts collected in step 1 of SKILL.md. Lines marked `(Paddle)` are there because a Paddle document asks for them; `references/REQUIREMENTS.md` has the source for each. Remove the markers before publishing. Everything else is ordinary consumer terms and is yours to adapt.

Not legal advice. These are working pages that a seller publishes; have the liability, governing law and consumer-rights sections read by a lawyer for your jurisdiction and your buyers'.

- [Placeholders](#placeholders)
- [Terms and Conditions](#terms-and-conditions)
- [Refund Policy](#refund-policy)
- [Privacy Policy](#privacy-policy)

## Placeholders

| Placeholder | Value |
| --- | --- |
| `{{LEGAL_NAME}}` | Exactly as registered on the Paddle account. Company name, or the sole proprietor's legal name |
| `{{BRAND}}` | Trading name if different from the legal name; otherwise the same |
| `{{SITE_URL}}` | `https://example.com` |
| `{{PRODUCT_DESCRIPTION}}` | One sentence: what is sold, as software or digital goods |
| `{{SUPPORT_EMAIL}}` | Monitored address that can receive replies |
| `{{SUPPORT_PHONE}}` | Required by the handbook alongside the email |
| `{{COUNTRY}}` | Principal place of business |
| `{{REFUND_DAYS}}` | Integer. Paddle recommends 30; 14 is the statutory floor for EU and UK buyers |
| `{{DATA_COLLECTED}}` | Bullet list of what the product actually collects |
| `{{THIRD_PARTIES}}` | Table rows of vendors actually used, each with its privacy policy link |
| `{{LAST_UPDATED}}` | Date the page was last changed, shown at the top |

## Terms and Conditions

```markdown
# Terms and Conditions

Last updated: {{LAST_UPDATED}}

These Terms and Conditions ("Terms") govern your use of {{BRAND}} at {{SITE_URL}} (the "Service"), operated by **{{LEGAL_NAME}}** ("we", "us", "our"). By using the Service or purchasing a Product, you agree to these Terms and to our Privacy Policy and Refund Policy.

## About us

- **Legal name:** {{LEGAL_NAME}}                                      (Paddle)
- **Website:** {{SITE_URL}}
- **Support:** {{SUPPORT_EMAIL}}, {{SUPPORT_PHONE}}                     (Paddle)
- **Principal place of business:** {{COUNTRY}}

## About the Service

{{PRODUCT_DESCRIPTION}} You purchase access to a Product, download it or receive a licence or account access, and use it in your own projects under the licence attached to that Product.

## Purchases and billing

Our order process is conducted by our online reseller Paddle.com. Paddle.com is the Merchant of Record for all our orders. Paddle provides all customer service inquiries and handles returns.   (Paddle, verbatim)

- All purchases are sold and processed by **Paddle.com Market Limited** and its affiliates (collectively, "Paddle"). When you buy, Paddle is the seller of record and your counterparty for the transaction. Paddle handles billing, payment processing, sales tax and VAT, invoicing and chargebacks.
- By completing a purchase you also agree to the [Paddle Buyer Terms](https://www.paddle.com/legal/buyer-terms). Your payment card details are handled by Paddle and never reach our servers.
- Prices are shown exclusive of tax. Applicable sales tax or VAT is calculated and collected by Paddle at checkout based on your billing location.
- Prices may change; changes do not affect orders already placed.
- Refunds are governed by our [Refund Policy]({{SITE_URL}}/refund) and are issued by Paddle.

## Licence

When you purchase a Product you receive the licence stated on that Product's page. Unless that page says otherwise, you may use and modify the Product in your own personal and commercial projects and deploy the result as part of your application. You may not resell, redistribute or sublicense the Product as-is, share it publicly, or claim ownership of it. Where a Product page and these Terms conflict, the Product page governs that Product.

## Accounts

You are responsible for activity under your account and for keeping it secure. You must be at least 13 years old to create one. We may suspend accounts that violate these Terms; Products already downloaded remain yours to use under their licence.

## Acceptable use

You may not share download links or credentials to bypass payment, scrape or systematically extract Products, circumvent licence checks, or use the Service for unlawful purposes.

## No warranty

The Service and Products are provided "as is" without warranties of any kind, express or implied, including fitness for a particular purpose and freedom from defects.

## Limitation of liability

To the maximum extent permitted by law, we are not liable for indirect, incidental or consequential damages, and our total liability is limited to the amount you paid us in the twelve months before the claim or USD 100, whichever is greater.

## Chargebacks

If you have a problem with a purchase, contact {{SUPPORT_EMAIL}} or request a refund through Paddle before opening a chargeback with your bank. We will work with you and with Paddle to resolve it. Fraudulent chargebacks may result in termination of your account and licence.

## Third-party services

We rely on third parties including Paddle (Merchant of Record) and the providers listed in our Privacy Policy. Their terms and privacy policies apply to their services.

## Governing law

These Terms are governed by the laws of {{COUNTRY}}. Because Paddle is the Merchant of Record, disputes about a purchase transaction may also be subject to the Paddle Buyer Terms.

## Changes

We may update these Terms. Changes take effect when posted here with a new "Last updated" date, with reasonable notice for material changes.

## Contact

**{{LEGAL_NAME}}**, {{SUPPORT_EMAIL}}, {{SUPPORT_PHONE}}
```

## Refund Policy

The first section is the one the reviewer reads. Keep it to the window and nothing else.

```markdown
# Refund Policy

Last updated: {{LAST_UPDATED}}

## {{REFUND_DAYS}}-day refund window

You may request a full refund within **{{REFUND_DAYS}} days** of your purchase, for any reason. You do not need to justify the request, and downloading a Product or activating its licence does not affect your eligibility.

## How to request a refund

Our Products are sold by **Paddle.com Market Limited** and its affiliates (collectively, "Paddle") as Merchant of Record, so Paddle issues refunds.   (Paddle)

The fastest route is Paddle directly:

1. Go to [paddle.net](https://paddle.net)
2. Enter the email address you used at checkout
3. Find your order and choose Request refund

You can also email **{{SUPPORT_EMAIL}}** with the email address used at checkout, the Product name and, if you have it, the Paddle order reference. We reply within two business days.

## How refunds are processed

Refunds are issued by Paddle to your original payment method. Card refunds usually appear within 3 to 5 working days; PayPal refunds within 48 hours.   (Paddle)

When a refund is issued, the licence for the Product ends and you agree to stop using it.

## Chargebacks

Please contact us or request a refund through Paddle before opening a chargeback with your bank. We will resolve it with you and with Paddle. Chargebacks filed without contacting us first may result in termination of your account.

## Contact

**{{LEGAL_NAME}}**, {{SUPPORT_EMAIL}}, {{SUPPORT_PHONE}}
```

Words that must not appear in the refund window section: if, unless, except, discretion, eligible, non-refundable, processing fee, subject to, may be. The verification script in SKILL.md greps for them near the number.

## Privacy Policy

```markdown
# Privacy Policy

Last updated: {{LAST_UPDATED}}

**{{LEGAL_NAME}}** ("we", "us", "our") operates {{BRAND}} at {{SITE_URL}}. This policy explains what we collect, why, and the choices you have. We do not sell personal data.

**We are the data controller** for personal data collected through the Service. For payment data, Paddle is an independent controller; see Payment information below.

Principal place of business: {{COUNTRY}}. Privacy requests: {{SUPPORT_EMAIL}}.

## What we collect

### Account and usage data

{{DATA_COLLECTED}}

### Payment information

All purchases are sold and processed by **Paddle.com Market Limited** and its affiliates (collectively, "Paddle"), the Merchant of Record for our transactions. Paddle collects the name, billing address, payment method, transaction data, and device and IP information it needs to process payment, determine tax and prevent fraud. Paddle is an independent data controller for that data; see [Paddle's Privacy Notice](https://www.paddle.com/legal/privacy).   (Paddle)

From Paddle we receive only the order status (paid, refunded, charged back), Paddle customer and order identifiers, and the billing email. We never store card numbers.

## How we use data

Delivering what you bought, managing your account and licences, answering support and refund requests, securing the Service, improving it, and meeting legal obligations. We do not send marketing email without opt-in, share data for others' marketing, or build advertising profiles.

## Cookies

Essential cookies for sign-in, session and checkout. State here whether analytics cookies exist and which vendor sets them.

## Retention

Account data while the account is active and for 30 days after deletion, except records we must keep for tax and accounting. Purchase records are kept by Paddle for the period tax law requires. Server logs for up to 90 days.

## Your rights

Access, correction, deletion, portability, objection, and withdrawal of consent, subject to local law. Email {{SUPPORT_EMAIL}}; we respond within one month. EU residents may also complain to their data protection authority. California residents have the rights listed under the CCPA; we do not sell personal data.

## Third-party services

| Service | Purpose | Privacy policy |
| --- | --- | --- |
| Paddle | Merchant of Record: billing, payment processing, tax, invoicing, fraud prevention | https://www.paddle.com/legal/privacy |
{{THIRD_PARTIES}}

## International transfers

Where data leaves your region we rely on appropriate safeguards such as Standard Contractual Clauses.

## Children

The Service is not directed at children under 13 and we do not knowingly collect their data.

## Changes

We post updates here with a new "Last updated" date and email account holders about material changes.

## Contact

**{{LEGAL_NAME}}**, {{SUPPORT_EMAIL}}, {{SUPPORT_PHONE}}, {{SITE_URL}}
```
