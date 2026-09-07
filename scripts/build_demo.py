from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

from psp_crm.synthetic_data import generate, Paths
from psp_crm.database import rebuild_database
from psp_crm.validation import run_quality_checks
from psp_crm.health_score import calculate_health_scores
from psp_crm.automations import run_all
from psp_crm.kpis import sales_kpis, revenue_kpis, funnel

if __name__ == '__main__':
    generate(Paths(Path('data/raw'), Path('data/processed')))
    counts = rebuild_database()
    quality = run_quality_checks()
    health = calculate_health_scores()
    automation = run_all()
    funnel().to_csv('data/processed/sales_funnel.csv', index=False)
    Path('reports').mkdir(exist_ok=True)
    Path('reports/build_summary.md').write_text(
        '# PSP Flow CRM Build Summary\n\n'
        f'Loaded table counts: {counts}\n\n'
        f'Sales KPIs: {sales_kpis()}\n\n'
        f'Revenue KPIs: {revenue_kpis()}\n\n'
        f'Automation run: {automation}\n\n'
        f'Data-quality checks: {len(quality)} checks with {int(quality.issue_count.sum())} flagged synthetic issues.\n'
        f'Customer health rows: {len(health)}\n',
        encoding='utf-8'
    )
    print('Demo built successfully.')
    print('Counts:', counts)
    print('Automation:', automation)
