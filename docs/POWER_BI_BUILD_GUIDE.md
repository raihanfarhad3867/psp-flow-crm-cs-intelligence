# Power BI build guide

Power BI Desktop cannot be executed in this environment, so this repository provides CSV exports and DAX-ready metric definitions.

## Import tables
Load all CSV files from `data/processed/` into Power BI.

Recommended relationships:
- companies[company_id] → contacts[company_id]
- companies[company_id] → leads[company_id]
- companies[company_id] → deals[company_id]
- companies[company_id] → subscriptions[company_id]
- companies[company_id] → usage_events[company_id]
- subscriptions[subscription_id] → onboarding[subscription_id]
- subscriptions[subscription_id] → support_tickets[subscription_id]
- owners[owner_id] → leads[owner_id]
- owners[owner_id] → deals[owner_id]
- products_plans[plan_id] → subscriptions[plan_id]

## Example DAX measures

```DAX
Total Pipeline EUR = SUM(deals[amount_eur])
Weighted Pipeline EUR = SUM(deals[weighted_amount_eur])
Won Revenue EUR = CALCULATE(SUM(deals[amount_eur]), deals[stage] = "Won")
Closed Deals = CALCULATE(COUNTROWS(deals), deals[stage] IN {"Won", "Lost"})
Won Deals = CALCULATE(COUNTROWS(deals), deals[stage] = "Won")
Win Rate = DIVIDE([Won Deals], [Closed Deals])
MRR EUR = SUM(subscriptions[mrr_eur]) + SUM(subscriptions[expansion_mrr_eur])
ARR EUR = [MRR EUR] * 12
Churned MRR EUR = CALCULATE(SUM(subscriptions[mrr_eur]), subscriptions[status] = "Churned")
Expansion MRR EUR = SUM(subscriptions[expansion_mrr_eur])
Gross Revenue Retention = DIVIDE(SUM(subscriptions[mrr_eur]) - [Churned MRR EUR], SUM(subscriptions[mrr_eur]))
Net Revenue Retention = DIVIDE(SUM(subscriptions[mrr_eur]) - [Churned MRR EUR] + [Expansion MRR EUR], SUM(subscriptions[mrr_eur]))
```

## Recommended pages
1. Executive Overview: MRR, ARR, pipeline, win rate, NRR, at-risk accounts.
2. Sales Funnel: stage conversion, weighted pipeline, stalled deals.
3. Customer Success: health distribution, renewals, support tickets, onboarding.
4. Data Quality: duplicate, missing, orphan, invalid-date issues.
