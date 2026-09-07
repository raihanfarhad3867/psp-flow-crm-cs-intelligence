# PSP Flow — CRM & Customer Success Intelligence

A reproducible Python, SQL and Streamlit prototype for exploring CRM data quality, sales operations and customer-success decision support in a fictional B2B logistics-automation business.

**Data scope:** All business records and financial figures are synthetic. This is a technical demonstration, not a production CRM or evidence of real customers or revenue.

## What the project includes

- Synthetic CRM data generation and a relational SQLite model.
- Sales pipeline, activity and customer-success reporting.
- Rule-based account-health scoring and workflow task logic.
- Data-quality checks and reproducible tests.
- A read-only HubSpot API client with pagination, retries, association reads and a separate local snapshot.
- A Streamlit interface for the synthetic dataset and CRM snapshot exploration.

## Current verification

Real HubSpot connected-tool operations were verified using a clearly labelled synthetic company, contact, deal and two tasks, including their associations. The application-level authenticated API synchronization has not been independently verified against the portal. No production deployment, real commercial impact or validated churn-prediction performance is claimed.

## Running locally

The source tree is being prepared from the original project archive. Once the source is published, install the requirements, run `python scripts/build_demo.py`, then `python -m pytest -q` and `streamlit run app.py`. The HubSpot integration is optional and requires a separately authorized local token. Never commit credentials or real customer exports.

The implementation and documentation will be published as normal source files rather than a ZIP-only repository.