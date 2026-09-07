# CRM object definitions and lifecycle design

## Lead
A lead is a potential buyer signal, such as a website inquiry, outbound response, referral, or event contact. A lead may be unqualified and should not be treated as an active sales opportunity until basic fit and interest are confirmed.

## Contact
A contact is an individual person associated with a company. Contacts can be decision-makers, influencers, admins, or users. A single company can have many contacts.

## Company
A company is the account-level organization. In B2B CRM design, company is the stable account entity that connects contacts, deals, subscriptions, tickets, activities, and customer success work.

## Deal
A deal is a commercial opportunity attached to a company. It has a sales stage, amount, probability, expected close date, owner, and outcome.

## Customer
A customer is a company with at least one won deal and active or historical subscription.

## Subscription
A subscription is the commercial service contract after a deal is won. It contains plan, MRR, ARR, renewal date, status, and expansion/churn fields.

## Sales lifecycle
New Lead → Qualified → Demo → Proposal → Negotiation → Won/Lost

## Customer lifecycle
Won → Onboarding → Active → At Risk → Renewal / Expansion / Churn

## Data governance rules
- Use controlled picklists for source, lifecycle stage, deal stage, ticket priority, and status.
- Use company_id as the main account key.
- Use contact email as a deduplication signal, but do not depend on email alone for all identity management.
- Do not create a subscription unless the deal is won.
- Do not create customer-success renewal tasks for non-customers.
- Treat customer health as decision support, not a validated prediction model.
