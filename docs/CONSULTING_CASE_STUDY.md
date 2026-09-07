# Portfolio case study

## Business problem
A logistics-automation SaaS business needs better coordination between Sales, Customer Success, and management reporting. Leads and deals must be tracked consistently, customers need structured onboarding, and account risks should be visible before renewal.

## Objectives
- Design a B2B CRM data model.
- Build a reproducible Python/SQL data pipeline.
- Create revenue and customer-success KPIs.
- Implement workflow automations.
- Provide an account-level briefing for customer-success reviews.

## Stakeholders
- Sales manager: pipeline visibility, stage conversion, stalled deals.
- Customer success manager: onboarding, support issues, health, renewals.
- RevOps analyst: clean data model, validation, reporting definitions.
- Management: KPI summary, risks, recommendations.

## Current-state process
Lead capture, deal updates, onboarding tasks, usage review, and support tracking are fragmented. Data-quality issues create reporting friction and slow follow-up.

## Future-state process
A normalized CRM database connects account, contact, deal, subscription, support, usage, and task data. Automations create follow-up tasks and health alerts. Dashboards give one operating view.

## Results from synthetic demo
The project produces a working SQLite database, Streamlit app, data-quality report, sales funnel, revenue KPIs, customer-health scoring, workflow logs, and AI-assisted account briefings. All outputs are reproducible from synthetic data.

## Limitations
- Data is synthetic.
- Health score is illustrative and not a trained churn model.
- Live HubSpot/Salesforce integration requires local credentials and explicit authorization.
- Power BI file generation is not automated in this environment; Power BI-ready CSVs and measure definitions are included.

## Future improvements
- Add real HubSpot private app sync in a sandbox portal.
- Add dbt-style transformations and model tests.
- Add Power BI PBIX file built manually from exported tables.
- Add role-based access and audit logging.
