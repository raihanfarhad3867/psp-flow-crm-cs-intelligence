# Automation workflow documentation

## Workflow 1: Lead Routing
Trigger: new lead with missing owner.

Steps:
1. Validate that the lead exists in the CRM database.
2. Assign a sales owner using a simple round-robin rule.
3. Create a first follow-up task due the next day.
4. Log the workflow result in `automation_log`.

Controls:
- Uses deterministic task IDs for duplicate prevention.
- Does not send real emails.
- Does not write to live CRM without local configuration.

## Workflow 2: Customer Onboarding
Trigger: won subscription with no onboarding record.

Steps:
1. Create onboarding record.
2. Create kickoff, import, configuration, and training tasks.
3. Assign Customer Success owner.
4. Log workflow result.

Controls:
- Uses `INSERT OR IGNORE` for idempotency.
- Keeps onboarding tasks visible in the dashboard.

## Workflow 3: At-Risk Alert
Trigger: customer health score classified as At Risk.

Steps:
1. Recalculate health score from usage, onboarding, support, and renewal signals.
2. Create at-risk customer review task.
3. Log account-level risk reason.

Controls:
- Transparent rule-based model.
- No automated customer contact.
- Human review required before action.
