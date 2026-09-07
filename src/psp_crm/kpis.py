from __future__ import annotations

from pathlib import Path
import sqlite3
import pandas as pd

DB = Path('data/psp_flow_crm.db')
STAGE_ORDER = ['New Lead','Qualified','Demo','Proposal','Negotiation','Won','Lost']


def connection(db_path: Path = DB):
    return sqlite3.connect(db_path)


def sales_kpis(db_path: Path = DB) -> dict:
    with connection(db_path) as conn:
        deals = pd.read_sql('SELECT * FROM deals', conn, parse_dates=['created_at','expected_close_date','closed_at'])
        leads = pd.read_sql('SELECT * FROM leads', conn, parse_dates=['created_at','first_response_at'])
        activities = pd.read_sql('SELECT * FROM activities', conn, parse_dates=['activity_date'])

    open_deals = deals[~deals.stage.isin(['Won','Lost'])]
    won = deals[deals.stage == 'Won']
    closed = deals[deals.stage.isin(['Won','Lost'])]
    avg_response_hours = ((leads.first_response_at - leads.created_at).dt.total_seconds() / 3600).mean()
    kpi = {
        'total_pipeline_eur': round(open_deals.amount_eur.sum(), 2),
        'weighted_pipeline_eur': round(open_deals.weighted_amount_eur.sum(), 2),
        'won_revenue_eur': round(won.amount_eur.sum(), 2),
        'win_rate': round(len(won) / len(closed), 3) if len(closed) else 0,
        'average_lead_response_hours': round(avg_response_hours, 1),
        'stalled_open_deals': int(((pd.Timestamp('2026-09-07') - open_deals.created_at).dt.days > 45).sum()),
        'activities_logged': int(len(activities)),
    }
    return kpi


def funnel(db_path: Path = DB) -> pd.DataFrame:
    with connection(db_path) as conn:
        deals = pd.read_sql('SELECT stage, amount_eur FROM deals', conn)
    rows = []
    for stage in STAGE_ORDER:
        subset = deals[deals.stage == stage]
        rows.append({'stage': stage, 'deal_count': len(subset), 'amount_eur': subset.amount_eur.sum()})
    df = pd.DataFrame(rows)
    first = max(df.deal_count.iloc[0], 1)
    df['conversion_from_first_stage'] = (df.deal_count / first).round(3)
    return df


def revenue_kpis(db_path: Path = DB) -> dict:
    with connection(db_path) as conn:
        subs = pd.read_sql('SELECT * FROM subscriptions', conn, parse_dates=['renewal_date'])
    active = subs[subs.status != 'Churned']
    beginning_mrr = subs.mrr_eur.sum()
    churned_mrr = subs.loc[subs.status == 'Churned', 'mrr_eur'].sum()
    expansion_mrr = subs.expansion_mrr_eur.sum()
    current_mrr = active.mrr_eur.sum() + active.expansion_mrr_eur.sum()
    grr = (beginning_mrr - churned_mrr) / beginning_mrr if beginning_mrr else 0
    nrr = (beginning_mrr - churned_mrr + expansion_mrr) / beginning_mrr if beginning_mrr else 0
    return {
        'mrr_eur': round(current_mrr, 2),
        'arr_eur': round(current_mrr * 12, 2),
        'churned_mrr_eur': round(churned_mrr, 2),
        'expansion_mrr_eur': round(expansion_mrr, 2),
        'gross_revenue_retention': round(grr, 3),
        'net_revenue_retention': round(nrr, 3),
        'renewals_next_90_days': int(((subs.renewal_date - pd.Timestamp('2026-09-07')).dt.days.between(0,90)).sum()),
    }
