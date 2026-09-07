from __future__ import annotations

from pathlib import Path
import sqlite3
import pandas as pd

TODAY = pd.Timestamp('2026-09-07')
DB = Path('data/psp_flow_crm.db')


def calculate_health_scores(db_path: Path = DB) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        subs = pd.read_sql('SELECT * FROM subscriptions', conn, parse_dates=['renewal_date'])
        onboarding = pd.read_sql('SELECT * FROM onboarding', conn)
        usage = pd.read_sql('SELECT * FROM usage_events', conn, parse_dates=['event_month','last_login_date'])
        tickets = pd.read_sql('SELECT * FROM support_tickets', conn)
        companies = pd.read_sql('SELECT company_id, company_name, segment, city FROM companies', conn)

    rows = []
    for _, sub in subs.iterrows():
        company_id = sub.company_id
        u = usage[usage.company_id == company_id].sort_values('event_month')
        if len(u) >= 2:
            recent = u.tail(1).shipments_processed.iloc[0]
            previous_avg = u.head(max(len(u)-1,1)).shipments_processed.mean()
            usage_ratio = recent / previous_avg if previous_avg else 0
        else:
            usage_ratio = 0
        usage_score = min(max(usage_ratio, 0), 1.25) / 1.25 * 35

        onb = onboarding[onboarding.company_id == company_id]
        onboarding_score = (onb.completion_pct.iloc[0] if len(onb) else 0) / 100 * 25

        open_tickets = tickets[(tickets.company_id == company_id) & (tickets.status != 'Resolved')]
        severe_open = open_tickets[open_tickets.priority.isin(['High','Critical'])]
        support_score = max(0, 20 - len(open_tickets) * 4 - len(severe_open) * 5)

        days_to_renewal = (sub.renewal_date - TODAY).days
        if days_to_renewal < 0:
            renewal_score = 0
        elif days_to_renewal <= 30:
            renewal_score = 8
        elif days_to_renewal <= 90:
            renewal_score = 14
        else:
            renewal_score = 20

        score = round(usage_score + onboarding_score + support_score + renewal_score, 1)
        if score >= 75:
            status = 'Healthy'
        elif score >= 65:
            status = 'Needs Attention'
        else:
            status = 'At Risk'
        rows.append({
            'company_id': company_id,
            'subscription_id': sub.subscription_id,
            'health_score': score,
            'health_status': status,
            'usage_score': round(usage_score,1),
            'onboarding_score': round(onboarding_score,1),
            'support_score': round(support_score,1),
            'renewal_score': round(renewal_score,1),
            'days_to_renewal': int(days_to_renewal),
            'reason': _reason(status, usage_ratio, len(open_tickets), days_to_renewal),
        })
    scores = pd.DataFrame(rows).merge(companies, on='company_id', how='left')
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    scores.to_csv('data/processed/customer_health_scores.csv', index=False)
    return scores


def _reason(status: str, usage_ratio: float, open_tickets: int, days_to_renewal: int) -> str:
    facts = []
    if usage_ratio < .75:
        facts.append('usage declined versus prior months')
    if open_tickets > 0:
        facts.append(f'{open_tickets} open support ticket(s)')
    if 0 <= days_to_renewal <= 90:
        facts.append('renewal approaching')
    if not facts:
        facts.append('stable usage and limited open risk signals')
    return f"{status}: " + '; '.join(facts)

if __name__ == '__main__':
    print(calculate_health_scores().head())
