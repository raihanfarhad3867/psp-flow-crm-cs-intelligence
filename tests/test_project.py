from pathlib import Path
import sys
import sqlite3

sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

from psp_crm.synthetic_data import generate, Paths
from psp_crm.database import rebuild_database
from psp_crm.validation import run_quality_checks
from psp_crm.kpis import sales_kpis, revenue_kpis, funnel
from psp_crm.health_score import calculate_health_scores
from psp_crm.automations import run_all, run_lead_routing
from psp_crm.account_brief import generate_account_brief
from psp_crm.crm_adapters import LocalCRMAdapter


def setup_module(module):
    generate(Paths(Path('data/raw'), Path('data/processed')))
    rebuild_database()


def test_database_tables_load():
    with sqlite3.connect('data/psp_flow_crm.db') as conn:
        company_count = conn.execute('SELECT COUNT(*) FROM companies').fetchone()[0]
        deal_count = conn.execute('SELECT COUNT(*) FROM deals').fetchone()[0]
    assert company_count == 80
    assert deal_count == 100


def test_quality_checks_detect_synthetic_issues():
    report = run_quality_checks()
    assert report.issue_count.sum() > 0
    assert 'invalid deal stage' in set(report.check_name)


def test_kpi_outputs_are_valid():
    s = sales_kpis()
    r = revenue_kpis()
    assert s['weighted_pipeline_eur'] >= 0
    assert 0 <= s['win_rate'] <= 1
    assert r['arr_eur'] >= 0
    assert 0 <= r['net_revenue_retention'] <= 2
    assert not funnel().empty


def test_health_scores_range_and_labels():
    scores = calculate_health_scores()
    assert scores.health_score.between(0, 100).all()
    assert set(scores.health_status).issubset({'Healthy','Needs Attention','At Risk'})


def test_automations_are_idempotent_enough():
    first = run_all()
    second_lead = run_lead_routing()
    assert first['at_risk_tasks_created'] >= 0
    assert second_lead == 0


def test_account_brief_grounded():
    scores = calculate_health_scores()
    company_id = scores.iloc[0].company_id
    brief = generate_account_brief(company_id)
    assert 'Facts from CRM data' in brief
    assert company_id not in brief or 'No account data' not in brief


def test_local_adapter_upsert_dedupes():
    adapter = LocalCRMAdapter()
    res = adapter.upsert('companies', [{'id': 'a'}, {'id': 'a'}, {'id': 'b'}], key='id')
    assert res.succeeded == 2
    assert res.failed == 1
