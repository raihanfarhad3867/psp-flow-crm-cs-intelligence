# Version 2 verification report

Date: 2026-09-07

## Completed
- Replaced the no-op HubSpot adapter with an authenticated requests-based REST client.
- Added paginated CRM reads, bounded retries, association batch reads, and an explicit write guard.
- Added a separate rerunnable live SQLite snapshot and CSV export pipeline.
- Added a read-only live-data viewer and local integration CLI.
- Rebuilt the original seeded synthetic demo successfully.
- Ran the full local test suite: **17 passed**.
- Tested actual HTTP request serialization, bearer authentication, rate-limit retry and pagination against a local test server.
- Verified that the new live sync does not duplicate records on rerun and reconciles removed associations in controlled tests.

## Not verified / remaining
- No authenticated request to the user's actual HubSpot portal was completed.
- No HubSpot production or sandbox write was performed.
- No real customer, revenue, or retention outcome is claimed.
- Streamlit browser startup could not be checked in this environment: the package was not installed and package installation failed because external package-index DNS was unavailable. Python source compilation passed; the dashboard requires a local smoke test.
- The project has not been published to GitHub. The existing account connection was readable, but no CRM repository was found and a repository-creation action was not available.
- The optional low-level demo upsert is not a completed sandbox write workflow; it requires a dedicated unique property and explicit authorization.

## Reproduce
```bash
python -m venv .venv
# Activate the environment, then:
pip install -r requirements.txt
python scripts/build_demo.py
python -m pytest -q
streamlit run app.py
```
For live verification, follow `docs/HUBSPOT_INTEGRATION.md` and use `python scripts/hubspot_cli.py check` before `sync`. Keep credentials and live data out of GitHub.
