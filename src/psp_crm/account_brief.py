from __future__ import annotations

from pathlib import Path
import sqlite3
import pandas as pd

from .health_score import calculate_health_scores

DB = Path('data/psp_flow_crm.db')


def generate_account_brief(company_id: str, db_path: Path = DB) -> str:
    scores = calculate_health_scores(db_path)
    with sqlite3.connect(db_path) as conn:
        company = pd.read_sql('SELECT * FROM companies WHERE company_id=?', conn, params=(company_id,))
        sub = pd.read_sql('SELECT * FROM subscriptions WHERE company_id=?', conn, params=(company_id,))
        tickets = pd.read_sql('SELECT * FROM support_tickets WHERE company_id=? ORDER BY created_at DESC', conn, params=(company_id,))
        activities = pd.read_sql('SELECT * FROM cs_activities WHERE company_id=? ORDER BY activity_date DESC LIMIT 3', conn, params=(company_id,))
        usage = pd.read_sql('SELECT * FROM usage_events WHERE company_id=? ORDER BY event_month DESC LIMIT 2', conn, params=(company_id,))
    if company.empty:
        return f"No account data found for {company_id}."
    c = company.iloc[0]
    s = scores[scores.company_id == company_id].iloc[0] if not scores[scores.company_id == company_id].empty else None
    sub_line = 'No active subscription in demo data.' if sub.empty else f"Plan subscription {sub.iloc[0].subscription_id}, status {sub.iloc[0].status}, MRR €{sub.iloc[0].mrr_eur:.0f}, renewal {sub.iloc[0].renewal_date}."
    open_tickets = tickets[tickets.status != 'Resolved'] if not tickets.empty else pd.DataFrame()
    last_usage = 'No usage events.' if usage.empty else f"Latest month processed {int(usage.iloc[0].shipments_processed)} shipments with {int(usage.iloc[0].automations_run)} automations."
    health = 'Health score unavailable.' if s is None else f"Health score {s.health_score}/100 ({s.health_status}). Reason: {s.reason}."
    recent_activity = 'No recent CS activity.' if activities.empty else '; '.join([f"{r.activity_date}: {r.activity_type}" for _, r in activities.iterrows()])
    suggestions = []
    if s is not None and s.health_status == 'At Risk':
        suggestions.append('Schedule a risk-review call and confirm the blocker owner.')
    if not open_tickets.empty:
        suggestions.append('Prioritise open high/critical support tickets before renewal discussion.')
    if s is not None and s.days_to_renewal <= 90:
        suggestions.append('Prepare renewal value summary and expansion fit check.')
    if not suggestions:
        suggestions.append('Continue normal QBR cadence and identify one expansion use case.')

    return f"""# AI-Assisted Account Brief — {c.company_name}

## Facts from CRM data
- Segment/location: {c.segment}, {c.city}, {c.country}.
- Subscription: {sub_line}
- Usage: {last_usage}
- Support: {len(open_tickets)} open ticket(s), {len(tickets)} total ticket(s) in demo data.
- Recent CS activity: {recent_activity}
- Health: {health}

## Suggested next actions for human review
- {' '.join(suggestions)}

Privacy note: this briefing is generated only from the synthetic/local CRM dataset in this portfolio project. It should be reviewed by a human before any customer communication.
"""
