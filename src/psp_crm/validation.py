from __future__ import annotations

from pathlib import Path
import pandas as pd

VALID_DEAL_STAGES = {'New Lead','Qualified','Demo','Proposal','Negotiation','Won','Lost'}
CANONICAL_SOURCES = {'website':'Website', 'linked in':'LinkedIn', 'linkedin':'LinkedIn'}


def run_quality_checks(raw_folder: Path = Path('data/raw'), processed_folder: Path = Path('data/processed')) -> pd.DataFrame:
    issues = []
    companies = pd.read_csv(raw_folder / 'companies_raw.csv')
    contacts = pd.read_csv(raw_folder / 'contacts_raw.csv')
    leads = pd.read_csv(raw_folder / 'leads_raw.csv')
    deals = pd.read_csv(raw_folder / 'deals_raw.csv')
    companies_clean = pd.read_csv(processed_folder / 'companies.csv')
    contacts_clean = pd.read_csv(processed_folder / 'contacts.csv')

    def add(table, check, severity, count, recommendation):
        issues.append({
            'table_name': table,
            'check_name': check,
            'severity': severity,
            'issue_count': int(count),
            'recommendation': recommendation,
        })

    add('companies_raw', 'duplicate company_id', 'High', companies.duplicated('company_id').sum(), 'Use company_id as upsert key; block duplicate insertions.')
    add('companies_raw', 'possible duplicate company_name', 'Medium', companies.duplicated('company_name').sum(), 'Add fuzzy matching review before creating a new company.')
    add('companies_raw', 'missing employee_count', 'Low', companies['employee_count'].isna().sum(), 'Route missing firmographic fields to enrichment queue.')
    add('companies_raw', 'unclean source values', 'Medium', companies['source'].astype(str).str.lower().isin(CANONICAL_SOURCES.keys()).sum(), 'Standardize source to a controlled picklist.')

    add('contacts_raw', 'duplicate email', 'High', contacts['email'].duplicated().sum(), 'Use email as contact dedupe key and merge interaction history.')
    valid_company_ids = set(companies_clean.company_id)
    add('contacts_raw', 'orphan contacts', 'High', (~contacts['company_id'].isin(valid_company_ids)).sum(), 'Reject contacts that do not belong to an existing company.')
    add('contacts_raw', 'missing email', 'Medium', contacts['email'].isna().sum(), 'Require email or verified phone before sales assignment.')

    valid_contact_ids = set(contacts_clean.contact_id)
    add('leads_raw', 'duplicate lead_id', 'High', leads.duplicated('lead_id').sum(), 'Use idempotent lead ingestion keyed on lead_id/source id.')
    add('leads_raw', 'missing contact_id', 'Medium', leads['contact_id'].isna().sum(), 'Create or enrich the contact before conversion to deal.')
    add('leads_raw', 'invalid contact reference', 'High', leads['contact_id'].notna().mul(~leads['contact_id'].isin(valid_contact_ids)).sum(), 'Validate contact-company relationship before sync.')
    add('leads_raw', 'missing first response', 'Medium', leads['first_response_at'].isna().sum(), 'Create SLA alert for leads without a first response timestamp.')

    add('deals_raw', 'invalid deal stage', 'High', (~deals['stage'].isin(VALID_DEAL_STAGES)).sum(), 'Reject stages outside the approved sales lifecycle.')
    add('deals_raw', 'negative deal amount', 'High', (deals['amount_eur'] < 0).sum(), 'Apply non-negative amount validation before load.')
    parsed_created = pd.to_datetime(deals['created_at'], errors='coerce')
    parsed_expected = pd.to_datetime(deals['expected_close_date'], errors='coerce')
    add('deals_raw', 'expected close before created date', 'High', (parsed_expected < parsed_created).sum(), 'Block invalid date transitions in the CRM/API layer.')

    report = pd.DataFrame(issues)
    Path('reports').mkdir(exist_ok=True)
    report.to_csv('reports/data_quality_report.csv', index=False)
    return report

if __name__ == '__main__':
    print(run_quality_checks())
