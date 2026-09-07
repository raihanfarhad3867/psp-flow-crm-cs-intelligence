"""Streamlit view for a live or verified HubSpot snapshot.

The snapshot is intentionally read-only and stored in a separate database from the
synthetic portfolio dataset.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

LIVE_DB = Path("data/hubspot_live.db")


def _load_records(db_path: Path) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        rows = pd.read_sql(
            """
            SELECT object_type, hubspot_id, properties_json, created_at, updated_at, last_seen_at
            FROM crm_records
            ORDER BY object_type, hubspot_id
            """,
            conn,
        )
    if rows.empty:
        return rows
    props = rows["properties_json"].apply(lambda raw: json.loads(raw or "{}"))
    expanded = pd.json_normalize(props)
    return pd.concat([rows.drop(columns=["properties_json"]), expanded], axis=1)


def _load_associations(db_path: Path) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql(
            """
            SELECT from_type, from_id, to_type, to_id, association_types_json
            FROM crm_associations
            ORDER BY from_type, from_id, to_type, to_id
            """,
            conn,
        )


def render_live(db_path: Path = LIVE_DB) -> None:
    """Render the HubSpot snapshot tab in Streamlit."""
    import streamlit as st
    st.subheader("Live HubSpot snapshot")
    st.caption(
        "Read-only view. Data is stored separately from the synthetic demo. "
        "Use `python scripts/hubspot_cli.py sync` for a token-based refresh, or "
        "`python scripts/load_verified_snapshot.py` for the included verified demo snapshot."
    )

    if not db_path.exists():
        st.warning(
            "No HubSpot snapshot database found. Run `python scripts/hubspot_cli.py sync` "
            "with a private app token, or run `python scripts/load_verified_snapshot.py`."
        )
        return

    try:
        records = _load_records(db_path)
        associations = _load_associations(db_path)
    except sqlite3.Error as exc:
        st.error(f"Could not read HubSpot snapshot: {exc}")
        return

    if records.empty:
        st.info("The HubSpot snapshot database exists but has no CRM records yet.")
        return

    counts = records.groupby("object_type").size().reset_index(name="records")
    st.dataframe(counts, use_container_width=True)

    deal_rows = records[records["object_type"].eq("deals")]
    if not deal_rows.empty:
        st.markdown("### Deals")
        cols = [c for c in ["hubspot_id", "dealname", "dealstage", "pipeline", "amount", "deal_currency_code", "created_at", "updated_at"] if c in deal_rows.columns]
        st.dataframe(deal_rows[cols], use_container_width=True)

    for object_type, label in [("companies", "Companies"), ("contacts", "Contacts"), ("tasks", "Tasks"), ("tickets", "Tickets")]:
        subset = records[records["object_type"].eq(object_type)]
        if subset.empty:
            continue
        st.markdown(f"### {label}")
        preferred = ["hubspot_id", "name", "firstname", "lastname", "email", "lifecyclestage", "hs_task_subject", "hs_task_status", "created_at", "updated_at"]
        cols = [c for c in preferred if c in subset.columns]
        st.dataframe(subset[cols] if cols else subset, use_container_width=True)

    if not associations.empty:
        st.markdown("### Associations")
        st.dataframe(associations.drop(columns=["association_types_json"], errors="ignore"), use_container_width=True)
