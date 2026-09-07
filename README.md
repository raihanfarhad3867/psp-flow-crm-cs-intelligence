# PSP Flow — CRM & Customer Success Intelligence

A reproducible Python, SQL and Streamlit prototype for CRM data quality, sales operations and customer-success decision support in a fictional B2B logistics-automation business.

**Scope:** All business records and financial figures are synthetic. This is a technical demonstration, not a production CRM or evidence of real customers, contracts or revenue.

## Capabilities

- Deterministic synthetic CRM dataset and relational SQLite model.
- Sales-pipeline, activity and customer-success reporting.
- Rule-based account-health scoring and workflow task logic.
- Data-quality checks for duplicates, missing fields, invalid values and relationships.
- Rule-based account briefings grounded in the local CRM data.
- Read-only HubSpot HTTP client with pagination, retries, association reads and a separate local snapshot.
- Streamlit interface for synthetic analytics and CRM snapshot exploration.

## Architecture

```text
Synthetic generator → CSV / SQLite → validation + KPI logic → Streamlit
                                           ↓
                                  health / task rules

HubSpot API → read-only synchronization → separate SQLite snapshot → viewer
```

The synthetic and HubSpot data stores are intentionally separate. The HubSpot connection is not required to run the demo.

## Quick start

Requires Python 3.11 or a compatible version.

```bash
python -m venv .venv
# Activate the virtual environment for your operating system.
python -m pip install -r requirements.txt
python scripts/build_demo.py
python -m pytest -q
streamlit run app.py
```

The build regenerates synthetic data and reports. Do not use the rebuild command against a database containing real customer data.

## HubSpot integration

A separately authorized local token is required for live API access. Copy `.env.example` to `.env` and configure the token privately. Do not commit it.

```bash
python scripts/hubspot_cli.py check
python scripts/hubspot_cli.py sync
python scripts/hubspot_cli.py export
```

These commands perform read-only CRM operations. Live snapshots and exports are excluded from version control. The low-level write adapter is disabled by default and is not a production synchronization service. See [integration documentation](docs/HUBSPOT_INTEGRATION.md).

## Verification and limitations

The synthetic build and **18 automated tests passed on GitHub Actions** during source publication. Tests cover the local pipeline and HubSpot transport behavior, including a local HTTP test server. This does not establish production readiness.

Real HubSpot connected-tool operations were separately verified using one labelled synthetic company, contact, deal and two tasks, including their associations. The application's own authenticated API synchronization has **not** been independently verified against the portal. The local test snapshot and live API integration are distinct.

Health scoring is rule-based decision support, not a validated churn-prediction model. Pipeline and retention metrics are demonstrations using synthetic data; they should not be interpreted as measured commercial performance. See the [KPI dictionary](docs/KPI_DICTIONARY.md) for definitions and the [case study](docs/CONSULTING_CASE_STUDY.md) for design context.

## Repository structure

```text
app.py                   Streamlit interface
src/psp_crm/             CRM model, analytics, scoring, workflows, API client
scripts/                Synthetic build and read-only HubSpot CLI
sql_schema.sql          SQLite schema
contracts.md            CRM object and lifecycle definitions
data/raw/                Deliberately imperfect synthetic inputs
data/processed/          Synthetic analytical extracts
data/powerbi/            Synthetic BI-ready extracts
docs/                    Technical and consulting documentation
reports/                 Synthetic build and quality reports
tests/                   Automated tests
```

No real customer exports, API credentials or private CRM databases are included in the source tree. The project does not claim production deployment, real revenue impact, Salesforce implementation or validated predictive AI.