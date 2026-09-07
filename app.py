from pathlib import Path
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent / 'src'))
from psp_crm.kpis import sales_kpis, revenue_kpis, funnel
from psp_crm.health_score import calculate_health_scores
from psp_crm.account_brief import generate_account_brief
from psp_crm.database import connect

DB = Path('data/psp_flow_crm.db')
st.set_page_config(page_title='PSP Flow CRM & Customer Success Intelligence', layout='wide')
st.title('PSP Flow – CRM & Customer Success Intelligence Platform')
st.caption('Synthetic B2B logistics-automation CRM demo. No real PSP Flow customer or financial data is used.')

source = st.sidebar.radio('Data source', ['Synthetic demo', 'Live HubSpot snapshot'])
if source == 'Live HubSpot snapshot':
    from psp_crm.live_dashboard import render_live
    render_live()
    st.stop()

if not DB.exists():
    st.error('Database not found. Run: python scripts/build_demo.py')
    st.stop()

sales = sales_kpis(DB)
rev = revenue_kpis(DB)
col1, col2, col3, col4 = st.columns(4)
col1.metric('Weighted Pipeline', f"€{sales['weighted_pipeline_eur']:,.0f}")
col2.metric('Win Rate', f"{sales['win_rate']*100:.1f}%")
col3.metric('MRR', f"€{rev['mrr_eur']:,.0f}")
col4.metric('NRR', f"{rev['net_revenue_retention']*100:.1f}%")

tab1, tab2, tab3, tab4, tab5 = st.tabs(['Sales Pipeline', 'Customer Success', 'Data Quality', 'Automations', 'Account Brief'])

with tab1:
    f = funnel(DB)
    st.subheader('Deal funnel')
    st.bar_chart(f.set_index('stage')['deal_count'])
    st.dataframe(f, use_container_width=True)
    with connect(DB) as conn:
        deals = pd.read_sql('SELECT deal_id, company_id, stage, amount_eur, weighted_amount_eur, expected_close_date, owner_id FROM deals ORDER BY amount_eur DESC', conn)
    st.subheader('Pipeline records')
    st.dataframe(deals, use_container_width=True)

with tab2:
    scores = calculate_health_scores(DB)
    st.subheader('Customer health')
    st.bar_chart(scores['health_status'].value_counts())
    st.dataframe(scores.sort_values('health_score'), use_container_width=True)

with tab3:
    qfile = Path('reports/data_quality_report.csv')
    if qfile.exists():
        q = pd.read_csv(qfile)
        st.subheader('Data-quality monitoring')
        st.dataframe(q, use_container_width=True)
    else:
        st.info('Run the build script to generate the data-quality report.')

with tab4:
    with connect(DB) as conn:
        logs = pd.read_sql('SELECT * FROM automation_log ORDER BY created_at DESC', conn)
        tasks = pd.read_sql('SELECT task_id, company_id, related_object, task_type, due_date, status, owner_id, created_by_workflow FROM tasks ORDER BY due_date', conn)
    st.subheader('Workflow execution log')
    st.dataframe(logs, use_container_width=True)
    st.subheader('Tasks created/tracked')
    st.dataframe(tasks, use_container_width=True)

with tab5:
    with connect(DB) as conn:
        companies = pd.read_sql('SELECT company_id, company_name FROM companies ORDER BY company_name', conn)
    option = st.selectbox('Select account', companies['company_id'], format_func=lambda cid: companies.set_index('company_id').loc[cid, 'company_name'])
    st.markdown(generate_account_brief(option, DB))
