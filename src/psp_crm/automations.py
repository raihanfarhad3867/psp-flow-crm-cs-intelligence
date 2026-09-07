from __future__ import annotations

from pathlib import Path
import sqlite3
from uuid import uuid4
import pandas as pd

from .health_score import calculate_health_scores

DB = Path('data/psp_flow_crm.db')
TODAY = pd.Timestamp('2026-09-07')


def _insert_log(conn, workflow, related_object, related_id, action, status, message):
    conn.execute(
        'INSERT OR IGNORE INTO automation_log(log_id, workflow_name, related_object, related_id, action, status, message) VALUES (?,?,?,?,?,?,?)',
        (str(uuid4()), workflow, related_object, related_id, action, status, message),
    )


def run_lead_routing(db_path: Path = DB) -> int:
    with sqlite3.connect(db_path) as conn:
        leads = pd.read_sql("SELECT * FROM leads WHERE owner_id IS NULL OR owner_id = ''", conn)
        owners = pd.read_sql("SELECT owner_id FROM owners WHERE team = 'Sales' ORDER BY owner_id", conn)
        created = 0
        for idx, lead in leads.iterrows():
            owner = owners.owner_id.iloc[idx % len(owners)]
            conn.execute('UPDATE leads SET owner_id=? WHERE lead_id=?', (owner, lead.lead_id))
            task_id = f"wf_lead_{lead.lead_id}"
            conn.execute("""
                INSERT OR IGNORE INTO tasks(task_id, company_id, related_object, related_id, task_type, due_date, status, owner_id, created_by_workflow)
                VALUES (?, ?, 'lead', ?, 'First follow-up', ?, 'Open', ?, 1)
            """, (task_id, lead.company_id, lead.lead_id, (TODAY + pd.Timedelta(days=1)).date().isoformat(), owner))
            _insert_log(conn, 'Lead Routing', 'lead', lead.lead_id, 'assign owner and create follow-up task', 'Success', f'Assigned to {owner}')
            created += 1
        conn.commit()
        return created


def run_customer_onboarding(db_path: Path = DB) -> int:
    with sqlite3.connect(db_path) as conn:
        won_without_onboarding = pd.read_sql("""
            SELECT s.subscription_id, s.company_id
            FROM subscriptions s
            LEFT JOIN onboarding o ON s.subscription_id = o.subscription_id
            WHERE o.onboarding_id IS NULL
        """, conn)
        created = 0
        for _, row in won_without_onboarding.iterrows():
            onb_id = f"wf_onb_{row.subscription_id}"
            conn.execute("""
                INSERT OR IGNORE INTO onboarding(onboarding_id, subscription_id, company_id, kickoff_date, target_go_live_date, completion_pct, status, owner_id)
                VALUES (?, ?, ?, ?, ?, 0, 'In Progress', 'own_003')
            """, (onb_id, row.subscription_id, row.company_id, TODAY.date().isoformat(), (TODAY + pd.Timedelta(days=30)).date().isoformat()))
            for step in ['Kickoff call', 'Import customer data', 'Configure workflow', 'Train key users']:
                conn.execute("""
                    INSERT OR IGNORE INTO tasks(task_id, company_id, related_object, related_id, task_type, due_date, status, owner_id, created_by_workflow)
                    VALUES (?, ?, 'onboarding', ?, ?, ?, 'Open', 'own_003', 1)
                """, (f"wf_task_{row.subscription_id}_{step[:3]}", row.company_id, onb_id, step, (TODAY + pd.Timedelta(days=7)).date().isoformat()))
            _insert_log(conn, 'Customer Onboarding', 'subscription', row.subscription_id, 'create onboarding plan', 'Success', 'Onboarding record and tasks created')
            created += 1
        conn.commit()
        return created


def run_at_risk_alerts(db_path: Path = DB) -> int:
    scores = calculate_health_scores(db_path)
    at_risk = scores[scores.health_status == 'At Risk']
    with sqlite3.connect(db_path) as conn:
        created = 0
        for _, row in at_risk.iterrows():
            task_id = f"wf_risk_{row.company_id}"
            conn.execute("""
                INSERT OR IGNORE INTO tasks(task_id, company_id, related_object, related_id, task_type, due_date, status, owner_id, created_by_workflow)
                VALUES (?, ?, 'company', ?, 'At-risk customer review', ?, 'Open', 'own_003', 1)
            """, (task_id, row.company_id, row.company_id, (TODAY + pd.Timedelta(days=2)).date().isoformat()))
            _insert_log(conn, 'At-Risk Alert', 'company', row.company_id, 'create customer-success review task', 'Success', row.reason)
            created += 1
        conn.commit()
        return created


def run_all(db_path: Path = DB) -> dict:
    return {
        'lead_routing_tasks_created': run_lead_routing(db_path),
        'onboarding_records_created': run_customer_onboarding(db_path),
        'at_risk_tasks_created': run_at_risk_alerts(db_path),
    }

if __name__ == '__main__':
    print(run_all())
