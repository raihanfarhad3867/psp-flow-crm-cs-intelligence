# User guide

## Build the demo
Run:

```bash
python scripts/build_demo.py
```

This regenerates synthetic data, rebuilds SQLite, runs data-quality checks, calculates health scores, runs workflow automations, and creates reports.

## Open the app
Run:

```bash
streamlit run app.py
```

## Review tabs
- Sales Pipeline: funnel, weighted pipeline, deal records.
- Customer Success: health scores, health statuses, risk reasons.
- Data Quality: flagged synthetic data-quality issues.
- Automations: workflow logs and tasks.
- Account Brief: generated account summary grounded in CRM data.

## Safe CRM integration
Use `.env.example` to configure secrets locally. Never commit `.env`. The default adapter is local-only and safe for portfolio review.
