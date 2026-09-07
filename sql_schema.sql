DROP TABLE IF EXISTS automation_log;
DROP TABLE IF EXISTS cs_activities;
DROP TABLE IF EXISTS support_tickets;
DROP TABLE IF EXISTS usage_events;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS onboarding;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS activities;
DROP TABLE IF EXISTS deals;
DROP TABLE IF EXISTS leads;
DROP TABLE IF EXISTS contacts;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS products_plans;
DROP TABLE IF EXISTS owners;

CREATE TABLE owners (
  owner_id TEXT PRIMARY KEY,
  owner_name TEXT NOT NULL,
  team TEXT NOT NULL CHECK(team IN ('Sales','Customer Success')),
  location TEXT NOT NULL
);

CREATE TABLE products_plans (
  plan_id TEXT PRIMARY KEY,
  plan_name TEXT NOT NULL UNIQUE,
  base_mrr_eur REAL NOT NULL CHECK(base_mrr_eur >= 0),
  description TEXT
);

CREATE TABLE companies (
  company_id TEXT PRIMARY KEY,
  company_name TEXT NOT NULL,
  segment TEXT NOT NULL,
  city TEXT NOT NULL,
  country TEXT NOT NULL,
  employee_count INTEGER,
  annual_shipments_est INTEGER,
  source TEXT,
  created_at TEXT NOT NULL,
  owner_id TEXT REFERENCES owners(owner_id)
);

CREATE TABLE contacts (
  contact_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  role TEXT,
  email TEXT UNIQUE,
  phone TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE leads (
  lead_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  contact_id TEXT REFERENCES contacts(contact_id),
  source TEXT,
  lifecycle_stage TEXT NOT NULL CHECK(lifecycle_stage IN ('New Lead','Qualified','Disqualified')),
  lead_score INTEGER CHECK(lead_score BETWEEN 0 AND 100),
  created_at TEXT NOT NULL,
  first_response_at TEXT,
  owner_id TEXT REFERENCES owners(owner_id)
);

CREATE TABLE deals (
  deal_id TEXT PRIMARY KEY,
  lead_id TEXT REFERENCES leads(lead_id),
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  deal_name TEXT NOT NULL,
  stage TEXT NOT NULL CHECK(stage IN ('New Lead','Qualified','Demo','Proposal','Negotiation','Won','Lost')),
  stage_probability REAL NOT NULL CHECK(stage_probability BETWEEN 0 AND 1),
  amount_eur REAL NOT NULL CHECK(amount_eur >= 0),
  weighted_amount_eur REAL NOT NULL CHECK(weighted_amount_eur >= 0),
  created_at TEXT NOT NULL,
  expected_close_date TEXT,
  closed_at TEXT,
  loss_reason TEXT,
  owner_id TEXT REFERENCES owners(owner_id)
);

CREATE TABLE activities (
  activity_id TEXT PRIMARY KEY,
  company_id TEXT REFERENCES companies(company_id),
  contact_id TEXT REFERENCES contacts(contact_id),
  deal_id TEXT REFERENCES deals(deal_id),
  activity_type TEXT NOT NULL,
  activity_date TEXT NOT NULL,
  outcome TEXT,
  owner_id TEXT REFERENCES owners(owner_id)
);

CREATE TABLE subscriptions (
  subscription_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  deal_id TEXT REFERENCES deals(deal_id),
  plan_id TEXT REFERENCES products_plans(plan_id),
  start_date TEXT NOT NULL,
  renewal_date TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('Active','At Risk','Churned')),
  mrr_eur REAL NOT NULL CHECK(mrr_eur >= 0),
  arr_eur REAL NOT NULL CHECK(arr_eur >= 0),
  expansion_mrr_eur REAL NOT NULL DEFAULT 0
);

CREATE TABLE onboarding (
  onboarding_id TEXT PRIMARY KEY,
  subscription_id TEXT NOT NULL REFERENCES subscriptions(subscription_id),
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  kickoff_date TEXT,
  target_go_live_date TEXT,
  actual_go_live_date TEXT,
  completion_pct INTEGER CHECK(completion_pct BETWEEN 0 AND 100),
  status TEXT NOT NULL CHECK(status IN ('In Progress','Delayed','Completed')),
  owner_id TEXT REFERENCES owners(owner_id)
);

CREATE TABLE tasks (
  task_id TEXT PRIMARY KEY,
  company_id TEXT REFERENCES companies(company_id),
  related_object TEXT,
  related_id TEXT,
  task_type TEXT NOT NULL,
  due_date TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('Open','Overdue','Done')),
  owner_id TEXT REFERENCES owners(owner_id),
  created_by_workflow BOOLEAN DEFAULT 0
);

CREATE TABLE usage_events (
  usage_event_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  subscription_id TEXT REFERENCES subscriptions(subscription_id),
  event_month TEXT NOT NULL,
  active_users INTEGER NOT NULL CHECK(active_users >= 0),
  shipments_processed INTEGER NOT NULL CHECK(shipments_processed >= 0),
  automations_run INTEGER NOT NULL CHECK(automations_run >= 0),
  last_login_date TEXT
);

CREATE TABLE support_tickets (
  ticket_id TEXT PRIMARY KEY,
  company_id TEXT REFERENCES companies(company_id),
  subscription_id TEXT REFERENCES subscriptions(subscription_id),
  created_at TEXT NOT NULL,
  priority TEXT NOT NULL CHECK(priority IN ('Low','Medium','High','Critical')),
  status TEXT NOT NULL CHECK(status IN ('Open','Pending','Resolved')),
  category TEXT
);

CREATE TABLE cs_activities (
  cs_activity_id TEXT PRIMARY KEY,
  company_id TEXT REFERENCES companies(company_id),
  activity_date TEXT NOT NULL,
  activity_type TEXT NOT NULL,
  notes TEXT,
  owner_id TEXT REFERENCES owners(owner_id)
);

CREATE TABLE automation_log (
  log_id TEXT PRIMARY KEY,
  workflow_name TEXT NOT NULL,
  related_object TEXT,
  related_id TEXT,
  action TEXT NOT NULL,
  status TEXT NOT NULL,
  message TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
