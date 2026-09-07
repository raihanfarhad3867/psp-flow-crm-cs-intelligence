# Live HubSpot verification

This project has two integration layers:

1. **Local HTTP connector** — implemented in `src/psp_crm/hubspot_api.py` and `src/psp_crm/hubspot_sync.py`. It supports authenticated read-only CRM snapshots, pagination, retries, association retrieval, and CSV exports. Writes are blocked by default.
2. **Real portal verification** — performed in the connected HubSpot portal **PSP Logistics BD Ltd.** using labelled synthetic records.

## Verified HubSpot actions

The following synthetic records were created in the real HubSpot portal on 2026-09-07:

| Object | HubSpot ID | Name |
|---|---:|---|
| Company | 446888694995 | PSP Flow Demo – Eastern Logistics |
| Contact | 862643029205 | Alex Morgan (Demo) |
| Deal | 520368224447 | PSP Flow Demo – Automation Pilot |
| Task | 517647733954 | [DEMO] Follow up on automation pilot |
| Task | 517685442752 | [DEMO] Prepare pilot onboarding checklist |

## Verified associations

- Contact → Company
- Deal → Company
- Deal → Contact
- Follow-up Task → Deal
- Follow-up Task → Contact
- Onboarding Task → Deal
- Onboarding Task → Company

## Scope and safety

All verified records are explicitly labelled as synthetic demo records. They do not represent real customers, real revenue, real contracts, or production CRM operations.

The local code does not store any API token. Token-based live sync requires a private app token configured locally in `.env`.

## Reproducing the reviewer snapshot without a token

```bash
python scripts/load_verified_snapshot.py
streamlit run app.py
```

Then choose **Live HubSpot snapshot** in the sidebar.

## Running a real local read-only sync

```bash
cp .env.example .env
# Add HUBSPOT_PRIVATE_APP_TOKEN locally; do not commit it.
python scripts/hubspot_cli.py check
python scripts/hubspot_cli.py sync
python scripts/hubspot_cli.py export
streamlit run app.py
```
