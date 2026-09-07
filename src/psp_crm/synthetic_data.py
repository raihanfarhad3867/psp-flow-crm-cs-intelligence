from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

SEED = 3867
TODAY = date(2026, 9, 7)

@dataclass(frozen=True)
class Paths:
    raw: Path
    processed: Path

OWNERS = [
    ("own_001", "Ayesha Rahman", "Sales", "Dhaka"),
    ("own_002", "Tariq Ahmed", "Sales", "Chittagong"),
    ("own_003", "Nusrat Chowdhury", "Customer Success", "Dhaka"),
    ("own_004", "Fahim Karim", "Customer Success", "Sylhet"),
]

PLANS = [
    ("plan_starter", "Starter", 250, "Small courier teams"),
    ("plan_growth", "Growth", 650, "Growing logistics operators"),
    ("plan_scale", "Scale", 1400, "Multi-branch logistics businesses"),
    ("plan_enterprise", "Enterprise", 3200, "Large logistics and distribution networks"),
]

CITIES = ["Dhaka", "Chittagong", "Sylhet", "Rajshahi", "Khulna", "Gazipur", "Narayanganj", "Cumilla"]
SEGMENTS = ["Courier", "E-commerce Fulfilment", "Retail Distribution", "3PL", "Cold Chain", "Pharma Distribution"]
SOURCES = ["Website", "Referral", "LinkedIn", "Partner", "Event", "Outbound", "website", "linked in", "Unknown", None]
DEAL_STAGES = ["New Lead", "Qualified", "Demo", "Proposal", "Negotiation", "Won", "Lost"]
STAGE_PROB = {"New Lead": .05, "Qualified": .12, "Demo": .18, "Proposal": .20, "Negotiation": .16, "Won": .21, "Lost": .08}
LOSS_REASONS = ["Price", "No budget", "No decision", "Competitor", "Timing", "Missing integration"]


def _id(prefix: str, n: int) -> str:
    return f"{prefix}_{n:04d}"


def _sample_stage(rng: np.random.Generator) -> str:
    return rng.choice(list(STAGE_PROB.keys()), p=list(STAGE_PROB.values())).item()


def generate(paths: Paths = Paths(Path("data/raw"), Path("data/processed")), seed: int = SEED) -> Dict[str, pd.DataFrame]:
    random.seed(seed)
    rng = np.random.default_rng(seed)
    paths.raw.mkdir(parents=True, exist_ok=True)
    paths.processed.mkdir(parents=True, exist_ok=True)

    owners = pd.DataFrame(OWNERS, columns=["owner_id", "owner_name", "team", "location"])
    plans = pd.DataFrame(PLANS, columns=["plan_id", "plan_name", "base_mrr_eur", "description"])

    company_rows: List[dict] = []
    for i in range(1, 81):
        segment = random.choice(SEGMENTS)
        city = random.choice(CITIES)
        size = int(rng.choice([12, 25, 45, 80, 140, 260, 520], p=[.13, .18, .21, .18, .15, .10, .05]))
        company_rows.append({
            "company_id": _id("co", i),
            "company_name": f"{random.choice(['Padma','Meghna','Jamuna','Shapla','Tiger','Nexa','Bengal','Delta','Rapid','Anchor'])} {random.choice(['Logistics','Courier','Fulfilment','Distribution','Express','Supply'])} {i}",
            "segment": segment,
            "city": city,
            "country": "Bangladesh",
            "employee_count": size,
            "annual_shipments_est": int(size * rng.integers(500, 2200)),
            "source": random.choice(SOURCES),
            "created_at": TODAY - timedelta(days=int(rng.integers(30, 620))),
            "owner_id": random.choice([o[0] for o in OWNERS[:2]]),
        })
    companies_clean = pd.DataFrame(company_rows)

    # Raw companies include deliberate duplicate and missing quality problems.
    companies_raw = pd.concat([companies_clean, companies_clean.iloc[[4, 11]].copy()], ignore_index=True)
    companies_raw.loc[3, "company_name"] = companies_raw.loc[4, "company_name"]  # fuzzy duplicate signal
    companies_raw.loc[7, "source"] = None
    companies_raw.loc[18, "employee_count"] = np.nan

    contact_rows: List[dict] = []
    roles = ["Founder", "Operations Manager", "Head of Logistics", "Sales Operations", "IT Manager"]
    for i, row in companies_clean.iterrows():
        for j in range(int(rng.choice([1, 1, 2, 2, 3]))):
            cid = row["company_id"]
            contact_rows.append({
                "contact_id": _id("ct", len(contact_rows) + 1),
                "company_id": cid,
                "first_name": random.choice(["Rahim", "Karim", "Nabila", "Sadia", "Imran", "Maliha", "Farhan", "Jarin"]),
                "last_name": random.choice(["Ahmed", "Rahman", "Hossain", "Khan", "Chowdhury", "Islam"]),
                "role": random.choice(roles),
                "email": f"contact{len(contact_rows)+1}@{str(row['company_name']).lower().replace(' ','').replace('&','')}bd.com",
                "phone": f"+8801{rng.integers(300000000, 999999999)}",
                "created_at": row["created_at"] + timedelta(days=int(rng.integers(0, 20))),
            })
    contacts_clean = pd.DataFrame(contact_rows)
    contacts_raw = contacts_clean.copy()
    contacts_raw.loc[10, "email"] = contacts_raw.loc[9, "email"]
    contacts_raw.loc[16, "company_id"] = "co_9999"
    contacts_raw.loc[25, "email"] = None

    lead_rows: List[dict] = []
    for i in range(1, 121):
        company = companies_clean.sample(1, random_state=seed + i).iloc[0]
        contact = contacts_clean[contacts_clean.company_id == company.company_id].sample(1, random_state=seed + i).iloc[0]
        created = TODAY - timedelta(days=int(rng.integers(1, 260)))
        first_response_hours = int(rng.choice([2, 4, 8, 18, 36, 72, 120], p=[.20,.22,.18,.15,.12,.08,.05]))
        lead_rows.append({
            "lead_id": _id("lead", i),
            "company_id": company.company_id,
            "contact_id": contact.contact_id,
            "source": random.choice(SOURCES),
            "lifecycle_stage": rng.choice(["New Lead", "Qualified", "Disqualified"], p=[.35, .50, .15]).item(),
            "lead_score": int(rng.integers(20, 96)),
            "created_at": created,
            "first_response_at": created + timedelta(hours=first_response_hours) if rng.random() > .07 else pd.NaT,
            "owner_id": random.choice([o[0] for o in OWNERS[:2]] + [None]),
        })
    leads_clean = pd.DataFrame(lead_rows)
    leads_raw = leads_clean.copy()
    leads_raw.loc[5, "source"] = "linked in"
    leads_raw.loc[6, "source"] = "website"
    leads_raw.loc[12, "contact_id"] = None
    leads_raw = pd.concat([leads_raw, leads_raw.iloc[[8]].copy()], ignore_index=True)

    deal_rows: List[dict] = []
    stage_rank = {s: i for i, s in enumerate(DEAL_STAGES)}
    for i in range(1, 101):
        lead = leads_clean.sample(1, random_state=seed + 200 + i).iloc[0]
        stage = _sample_stage(rng)
        amount = int(rng.choice([3000, 6000, 9000, 15000, 24000, 42000, 72000], p=[.10,.18,.21,.22,.15,.09,.05]))
        created = lead.created_at + timedelta(days=int(rng.integers(1, 35)))
        close = created + timedelta(days=int(rng.integers(10, 100))) if stage in ["Won", "Lost"] else pd.NaT
        deal_rows.append({
            "deal_id": _id("deal", i),
            "lead_id": lead.lead_id,
            "company_id": lead.company_id,
            "deal_name": f"PSP Flow rollout - {lead.company_id}",
            "stage": stage,
            "stage_probability": [0.05, .18, .35, .55, .75, 1.0, 0.0][stage_rank[stage]],
            "amount_eur": amount,
            "weighted_amount_eur": round(amount * [0.05, .18, .35, .55, .75, 1.0, 0.0][stage_rank[stage]], 2),
            "created_at": created,
            "expected_close_date": created + timedelta(days=int(rng.integers(25, 130))),
            "closed_at": close,
            "loss_reason": random.choice(LOSS_REASONS) if stage == "Lost" else None,
            "owner_id": lead.owner_id or random.choice([o[0] for o in OWNERS[:2]]),
        })
    deals_clean = pd.DataFrame(deal_rows)
    deals_raw = deals_clean.copy()
    deals_raw.loc[13, "stage"] = "Closed Maybe"
    deals_raw.loc[19, "expected_close_date"] = deals_raw.loc[19, "created_at"] - timedelta(days=3)
    deals_raw.loc[24, "amount_eur"] = -500

    activity_rows: List[dict] = []
    for i, deal in deals_clean.iterrows():
        num = int(rng.integers(1, 7))
        for _ in range(num):
            dt = deal.created_at + timedelta(days=int(rng.integers(0, 80)))
            activity_rows.append({
                "activity_id": _id("act", len(activity_rows) + 1),
                "company_id": deal.company_id,
                "contact_id": contacts_clean[contacts_clean.company_id == deal.company_id].sample(1, random_state=seed + len(activity_rows)).iloc[0].contact_id,
                "deal_id": deal.deal_id,
                "activity_type": rng.choice(["Call", "Email", "Demo", "Meeting", "Task"], p=[.22,.39,.10,.14,.15]).item(),
                "activity_date": dt,
                "outcome": rng.choice(["Completed", "No response", "Positive", "Rescheduled", "Follow-up needed"], p=[.36,.20,.19,.10,.15]).item(),
                "owner_id": deal.owner_id,
            })
    activities_clean = pd.DataFrame(activity_rows)

    sub_rows: List[dict] = []
    onboarding_rows: List[dict] = []
    task_rows: List[dict] = []
    usage_rows: List[dict] = []
    ticket_rows: List[dict] = []
    cs_rows: List[dict] = []
    won_deals = deals_clean[deals_clean.stage == "Won"].copy().reset_index(drop=True)
    for idx, deal in won_deals.iterrows():
        plan = plans.sample(1, random_state=seed + 500 + idx).iloc[0]
        start = pd.to_datetime(deal.closed_at).date() if pd.notna(deal.closed_at) else TODAY - timedelta(days=120)
        renewal = start + timedelta(days=365)
        mrr = int(plan.base_mrr_eur * rng.uniform(.85, 1.35))
        sub_rows.append({
            "subscription_id": _id("sub", idx + 1),
            "company_id": deal.company_id,
            "deal_id": deal.deal_id,
            "plan_id": plan.plan_id,
            "start_date": start,
            "renewal_date": renewal,
            "status": rng.choice(["Active", "Active", "Active", "At Risk", "Churned"], p=[.64,.12,.08,.11,.05]).item(),
            "mrr_eur": mrr,
            "arr_eur": mrr * 12,
            "expansion_mrr_eur": int(rng.choice([0, 0, 0, 80, 150, 300])),
        })
        completion = int(rng.choice([20, 45, 65, 80, 100], p=[.10,.20,.22,.26,.22]))
        onboarding_rows.append({
            "onboarding_id": _id("onb", idx + 1),
            "subscription_id": _id("sub", idx + 1),
            "company_id": deal.company_id,
            "kickoff_date": start + timedelta(days=3),
            "target_go_live_date": start + timedelta(days=30),
            "actual_go_live_date": start + timedelta(days=int(rng.integers(20, 55))) if completion == 100 else pd.NaT,
            "completion_pct": completion,
            "status": "Completed" if completion == 100 else rng.choice(["In Progress", "Delayed"]).item(),
            "owner_id": random.choice(["own_003", "own_004"]),
        })
        milestones = ["Kickoff", "Data Import", "User Training", "Workflow Setup", "Go-Live Review"]
        for m_i, ms in enumerate(milestones, 1):
            done = completion >= m_i * 20
            task_rows.append({
                "task_id": _id("task", len(task_rows) + 1),
                "company_id": deal.company_id,
                "related_object": "onboarding",
                "related_id": _id("onb", idx + 1),
                "task_type": ms,
                "due_date": start + timedelta(days=5 + 5 * m_i),
                "status": "Done" if done else rng.choice(["Open", "Overdue"], p=[.55,.45]).item(),
                "owner_id": random.choice(["own_003", "own_004"]),
                "created_by_workflow": False,
            })
        # six months of product usage events
        baseline = int(rng.integers(80, 900))
        decline = rng.random() < .25
        for month_back in range(5, -1, -1):
            month_start = date(TODAY.year, TODAY.month, 1) - pd.DateOffset(months=month_back)
            factor = (0.62 if decline and month_back <= 1 else 1.0) * rng.uniform(.75, 1.25)
            usage_rows.append({
                "usage_event_id": _id("use", len(usage_rows) + 1),
                "company_id": deal.company_id,
                "subscription_id": _id("sub", idx + 1),
                "event_month": pd.to_datetime(month_start).date(),
                "active_users": int(rng.integers(3, 55)),
                "shipments_processed": int(baseline * factor),
                "automations_run": int((baseline * factor) / rng.uniform(5, 12)),
                "last_login_date": TODAY - timedelta(days=int(rng.choice([1, 3, 7, 14, 32, 55], p=[.22,.25,.18,.15,.12,.08]))),
            })
        for _ in range(int(rng.choice([0,0,1,1,2,3], p=[.28,.20,.20,.18,.09,.05]))):
            ticket_rows.append({
                "ticket_id": _id("tic", len(ticket_rows) + 1),
                "company_id": deal.company_id,
                "subscription_id": _id("sub", idx + 1),
                "created_at": TODAY - timedelta(days=int(rng.integers(1, 120))),
                "priority": rng.choice(["Low", "Medium", "High", "Critical"], p=[.35,.36,.22,.07]).item(),
                "status": rng.choice(["Open", "Pending", "Resolved"], p=[.24,.22,.54]).item(),
                "category": rng.choice(["Integration", "Billing", "Training", "Bug", "Workflow design"]).item(),
            })
        cs_rows.append({
            "cs_activity_id": _id("cs", len(cs_rows) + 1),
            "company_id": deal.company_id,
            "activity_date": TODAY - timedelta(days=int(rng.integers(3, 80))),
            "activity_type": rng.choice(["QBR", "Training", "Renewal check", "Health review", "Escalation follow-up"]).item(),
            "notes": "Synthetic customer-success activity for portfolio demo.",
            "owner_id": random.choice(["own_003", "own_004"]),
        })

    dfs = {
        "owners": owners,
        "products_plans": plans,
        "companies": companies_clean,
        "contacts": contacts_clean,
        "leads": leads_clean,
        "deals": deals_clean,
        "activities": activities_clean,
        "subscriptions": pd.DataFrame(sub_rows),
        "onboarding": pd.DataFrame(onboarding_rows),
        "tasks": pd.DataFrame(task_rows),
        "usage_events": pd.DataFrame(usage_rows),
        "support_tickets": pd.DataFrame(ticket_rows),
        "cs_activities": pd.DataFrame(cs_rows),
    }
    raw_dfs = {
        "companies_raw": companies_raw,
        "contacts_raw": contacts_raw,
        "leads_raw": leads_raw,
        "deals_raw": deals_raw,
    }

    for name, df in dfs.items():
        df.to_csv(paths.processed / f"{name}.csv", index=False)
    for name, df in raw_dfs.items():
        df.to_csv(paths.raw / f"{name}.csv", index=False)

    return {**dfs, **raw_dfs}

if __name__ == "__main__":
    generate()
    print("Synthetic CRM dataset generated with fixed seed", SEED)
