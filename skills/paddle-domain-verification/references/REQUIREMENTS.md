# What Paddle actually requires

Every line here is quoted or closely paraphrased from a Paddle page, with the URL and the date it was read. Re-read the source before relying on a line if more than a few months have passed; Paddle revises these pages and the skill is only as good as its match with the current text.

Read: 2026-09-12.

- [Domain review](#domain-review)
- [Seller obligations from the handbook](#seller-obligations-from-the-handbook)
- [Refunds, as Paddle defines them](#refunds-as-paddle-defines-them)
- [Buyer Terms and Paddle entities](#buyer-terms-and-paddle-entities)
- [Privacy, who is the controller](#privacy-who-is-the-controller)
- [Acceptable Use Policy](#acceptable-use-policy)
- [What Paddle does not say](#what-paddle-does-not-say)

## Domain review

Source: <https://www.paddle.com/help/start/account-verification/what-is-domain-verification>

The domain must clearly display:

- "A clear description of your product or service"
- "Pricing details or a pricing page (a screenshot is acceptable if not yet available)"
- "Key features or deliverables included with the purchase"
- "Terms and Conditions, Refund Policy, and Privacy Policy (these must be clearly accessible via navigation on your website)"
- "Include the company name or sole proprietor's brand (legal name preferred for sole proprietors) in the Terms & Conditions"
- "Site must be live and secured with an SSL certificate (HTTPS)"
- "Custom/enterprise pricing sheet (if applicable)" as a downloadable PDF

Where to submit: the website approval section of the dashboard under Checkout, or the prompts on the get started page. "You can submit additional domains associated with your website for approval at any time."

Timing: "We automatically approve most domain submissions. If your submission requires a manual review by our team, this is typically completed within an estimated 5-7 business days."

Rejection reasons Paddle lists:

1. "The products being sold on the website are not in line with our Acceptable Use Policy"
2. "The domain being added was flagged as high risk and potentially does not follow our Terms & Conditions"
3. "Our team has requested more information about your website and we've not received a response from you"

Reasons seen in practice that are not on that list (seller report, April 2026, <https://dev.to/pavelbuild/paddle-rejected-my-saas-3-times-heres-what-they-check-that-isnt-in-their-docs-5dnn>, third party, treat as anecdote):

- "Refund policy contains qualifiers. Please provide unconditional refund terms matching our standard policy." The policy that was rejected said refunds were available "if the product fails to meet the described functionality" and that "processing fees may apply". The same policy passed once it read as an unconditional money-back window.
- "Legal entity on website doesn't match the registered entity on your Paddle account." The terms named a company; the Paddle account was a sole proprietor.
- "Your website advertises consulting services alongside the software product. Paddle processes digital goods only."

## Seller obligations from the handbook

Source: <https://www.paddle.com/seller-guides/seller-handbook>

Under "We require that our software sellers", the items that touch the website:

- "Have a website and only accept payments through their website, or apps using our SDKs."
- Display this text on the website Terms & Conditions, verbatim: "Our order process is conducted by our online reseller Paddle.com. Paddle.com is the Merchant of Record for all our orders. Paddle provides all customer service inquiries and handles returns"
- "Make it clear to buyers what products they're paying for and what amount they're committing to before the purchase."
- "List their terms & conditions, refund policy, and buyer support details (email and phone number) clearly on their website."
- "Include the company name or sole proprietor's brand (legal name preferred for sole proprietors) in the Terms & Conditions."
- "Make sure the buyer accepts their terms & conditions and refund policy before they make a purchase."
- "Notify us of any changes in your refund policy, product T&C or contact details."

Under recommended practices, not requirements:

- "Have at least a 30-day money-back guarantee as part of their refund policy."
- Maintain "a complaint policy with expected turnaround times for complaint resolution."
- Send a post-purchase email with activation details, the terms, the refund policy, support contact and a paddle.net link.

Note the gap between the two pages: the domain review page does not mention the phone number or the verbatim Merchant of Record sentence; the handbook requires both. Satisfy the handbook; it is the stricter document, and meeting it costs two sentences.

## Refunds, as Paddle defines them

Source: <https://www.paddle.com/legal/refund-policy> (effective 31 March 2026)

- Applies to "Transactions completed by Consumers and Businesses".
- Default position: "All Transactions are non-refundable and non-exchangeable", subject to statutory rights and Paddle's discretion.
- Statutory windows Paddle lists: 14 days for EU, EEA, Switzerland, UK, Turkey and Israel; 7 days for South Korea, Brazil, Canada and China; 5 days for Singapore.
- Discretionary: "Paddle may, at its sole discretion, issue a refund if a request is submitted within 14 days of your Transaction date".
- Buyers request refunds through the support link in the receipt or by visiting Paddle.net and selecting "Request refund".

Source: <https://www.paddle.com/help/manage/your-customers/how-do-i-issue-refunds>

- Sellers initiate refunds from the dashboard: Transactions, select the order, Refund, full or partial, with a reason.
- Card payments "can only be refunded on transactions less than 120 days old"; PayPal "if it is less than 179 days old".
- Card refunds take 3 to 5 working days to appear; PayPal within 48 hours.

What follows from the three sources together: your refund policy states a window that is at least the statutory 14 days Paddle already gives EU and UK buyers, ideally the 30 days Paddle recommends, and attaches no conditions to it. Paddle honours the statutory windows regardless of what your page says, so a shorter or conditional window buys nothing and costs the review.

## Buyer Terms and Paddle entities

Source: <https://www.paddle.com/legal/buyer-terms> (effective 31 March 2026). Link this URL, not older `/legal/checkout-buyer-terms` paths.

- "Paddle is an authorised reseller of Products for Suppliers, which means you purchase the Product from Paddle using our Services, and the Product is made available to you by the Supplier under the terms of their Supplier Agreement."
- Contracting entities by buyer location: Paddle.com Inc. (United States), Paddle.com (Canada) Ltd. (Canada), Paddle.com Market Limited (everywhere else; England and Wales, company number 8172165, 30 Old Bailey, London EC4M 7AU).

In your own pages, "Paddle.com Market Limited and its affiliates (collectively, Paddle)" covers all three without naming the wrong one for a given buyer.

## Privacy, who is the controller

Source: <https://www.paddle.com/legal/privacy> (last updated 16 March 2026)

- Paddle acts as a Controller, not a processor, for the personal data it collects at checkout. The controllers named are Paddle.com Market Limited, Paddle.com Inc., Paddle Payments Limited and Paddle.com Canada Ltd.
- Data Paddle collects includes invoice and payment records, billing address, payment method, cardholder name, card details, amount and date, plus geolocation and purchaser details.
- Paddle shares data with "Suppliers to the extent necessary to provide a product or service requested by you".

So your privacy policy names you as controller for your own data and Paddle as an independent controller for payment data, and links Paddle's notice. Paddle does not publish a requirement that you mention them in your privacy policy; the domain review page only requires that a privacy policy exists and is reachable. Mention them anyway, because it is true and because a reviewer looking for the payment relationship will look there.

## Acceptable Use Policy

Source: <https://www.paddle.com/help/start/intro-to-paddle/what-am-i-not-allowed-to-sell-on-paddle>

- "Paddle is built to serve software companies (including B2B SaaS, Consumer Software, and Games)."
- Prohibited, among others: "Physical products or products that require physical delivery"; "Human services that are not related to a software offering (e.g., pure consulting or advisory services, including but not limited to legal advice, coaching, IT services, and access to a community of experts)"; "Any product or service that enables non-Paddle Sellers to sell products and services to customers, such as digital marketplaces"; "Technical support services"; "Reseller Products, including but not limited to: Microsoft, Adobe".

Two of these bite ordinary indie sellers through wording alone. Calling your own store a "marketplace" reads as the prohibited third-party marketplace. Offering "done for you" or "managed" tiers reads as consulting. Neither is banned if the substance is software you built and sell yourself, but the page has to say so plainly.

## What Paddle does not say

Claims that circulate and are not in any Paddle source read on the date above:

- That the refund window must be exactly 14 days. Paddle recommends 30 and its own statutory minimum for EU and UK buyers is 14. State an exact number; the number is yours.
- That a refund page may contain no other clauses at all. The rejection wording targets conditions on the refund itself. A separate chargeback paragraph or a note that the licence ends on refund is a different clause. Keep such clauses out of the paragraph that states the window, so a reviewer scanning for conditions does not find them there.
- That Paddle requires GDPR wording. Paddle requires a privacy policy be present and reachable. GDPR obligations come from selling to EU residents, not from Paddle.
