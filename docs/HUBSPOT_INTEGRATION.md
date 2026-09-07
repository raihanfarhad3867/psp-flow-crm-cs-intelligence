# HubSpot integration — implementation and operating guide

## Scope and status
This version replaces the original no-op adapter with a real HTTP client and a read-only synchronization pipeline. It supports companies, contacts, deals, tickets, tasks, and selected associations. Authentication, pagination, retry handling, local persistence, reruns, and exports are implemented. Automated tests exercise the HTTP contract with controlled responses. A live customer-portal request has **not** been verified in this delivery. The ChatGPT HubSpot connection does not automatically expose its OAuth token to the local Python process.

## Safe setup
Use an isolated HubSpot developer/test account whenever possible. Create or authorize an app with the minimum relevant CRM read scopes. The exact scopes and object access depend on your account and product tier. Use an account-specific static access token or an authorized OAuth access token. Do not paste it into chat or commit it. The official documentation explains current authentication and scope requirements:

- https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/overview
- https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/scopes
- https://developers.hubspot.com/docs/apps/developer-platform/build-apps/manage-apps-in-hubspot

Copy `.env.example` to `.env`, set `HUBSPOT_PRIVATE_APP_TOKEN` locally, and install requirements. A ChatGPT plugin connection is separate from the application’s API credentials.

## Commands
```bash
python scripts/hubspot_cli.py check
python scripts/hubspot_cli.py sync
python scripts/hubspot_cli.py export
streamlit run app.py
```
Choose **Live HubSpot snapshot** in the sidebar. The check command makes one GET request for a company page. Sync reads permitted objects and association links; export produces separate local CSVs. The synthetic demo remains in `data/psp_flow_crm.db`; live records use `data/hubspot_live.db`.

## Mapping and behavior
The client uses the supported CRM v3 object endpoints and v4 association batch-read endpoint. It follows opaque `paging.next.after` cursors and retries HTTP 429 and transient 5xx responses with a bounded delay. 401/403 and other non-retryable errors fail clearly. The database upserts by `(object_type, hubspot_id)` and preserves source properties and association types. A rerun does not duplicate records. Completed pages are committed; a failure is recorded in `sync_runs`. The pipeline is a snapshot, not a historical change-data-capture system; deletions, archived records, full stage histories, and incremental checkpointing are not yet implemented.

## Writes and data protection
The normal client and all CLI commands are read-only. A guarded low-level batch upsert exists for explicitly authorized synthetic demonstrations, but no live write workflow is enabled by the CLI. It requires a dedicated unique `psp_demo_id` property and identifiers beginning `psp-demo-`. The property must be provisioned in an isolated account before use. No real customer records, emails, or production data should be modified for this portfolio.

Never publish the live SQLite database, exports, credentials, or real customer screenshots. Use the synthetic dataset for public GitHub screenshots and CV metrics. Restrict local file access and remove real snapshots when no longer required.

## Verification checklist
- [x] HTTP client and read-only permission guard implemented.
- [x] Pagination, retries, association reads, and rerunnable persistence tested with controlled responses.
- [x] Separate live database and export directory implemented.
- [ ] Authenticated live HubSpot GET verified.
- [ ] Actual portal scopes and accessible objects confirmed.
- [ ] Live association and data-mapping smoke test completed.
- [ ] Synthetic-only sandbox write and rerun verified, if write access is intentionally enabled.
- [ ] Actual live test evidence added to the portfolio.

## Troubleshooting
401: check the token and account authorization. 403: check object permissions and scopes. 429: retry budget exhausted; rerun later. A missing object scope may stop the sync; use `--objects companies contacts deals` to narrow the read. Never bypass permissions or use a production account to test destructive operations.
