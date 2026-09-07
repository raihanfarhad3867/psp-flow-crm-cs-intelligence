"""Read-only, transactional HubSpot snapshot and analytics exports.

Live data is intentionally kept separate from the reproducible synthetic demo.
"""
from __future__ import annotations
import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from .hubspot_api import HubSpotClient

OBJECTS = {
 'companies': ['name','domain','industry','city','country','numberofemployees','hubspot_owner_id','createdate','hs_lastmodifieddate','lifecyclestage'],
 'contacts': ['firstname','lastname','email','jobtitle','phone','lifecyclestage','hubspot_owner_id','createdate','hs_lastmodifieddate'],
 'deals': ['dealname','dealstage','pipeline','amount','closedate','createdate','hs_lastmodifieddate','hubspot_owner_id','hs_is_closed_won'],
 'tickets': ['subject','hs_pipeline','hs_pipeline_stage','hs_ticket_priority','createdate','hs_lastmodifieddate','hubspot_owner_id'],
 'tasks': ['hs_task_subject','hs_task_status','hs_task_priority','hs_timestamp','hs_task_body','hubspot_owner_id'],
}
ASSOCIATIONS = {'contacts':['companies'], 'deals':['companies','contacts'], 'tickets':['companies','contacts'], 'tasks':['companies','contacts','deals']}

def _now():
    return datetime.now(timezone.utc).isoformat()

def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute('PRAGMA foreign_keys=ON')
    return conn

def init(conn):
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS crm_records (
      object_type TEXT NOT NULL, hubspot_id TEXT NOT NULL, properties_json TEXT NOT NULL,
      created_at TEXT, updated_at TEXT, last_seen_at TEXT NOT NULL,
      PRIMARY KEY(object_type, hubspot_id));
    CREATE TABLE IF NOT EXISTS crm_associations (
      from_type TEXT NOT NULL, from_id TEXT NOT NULL, to_type TEXT NOT NULL, to_id TEXT NOT NULL,
      association_types_json TEXT NOT NULL,
      PRIMARY KEY(from_type,from_id,to_type,to_id));
    CREATE TABLE IF NOT EXISTS sync_runs (
      run_id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL, finished_at TEXT,
      status TEXT NOT NULL, counts_json TEXT, error TEXT);
    CREATE TABLE IF NOT EXISTS sync_state (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    ''')
    conn.commit()

def sync(client: HubSpotClient, db_path='data/hubspot_live.db', objects=None, include_associations=True):
    """Incrementally upsert records; replace associations for successfully read source objects.

    No CRM mutation is possible. An object page is committed atomically.
    """
    if Path(db_path).resolve() == Path('data/psp_flow_crm.db').resolve():
        raise ValueError('Live CRM data must not be synchronized into the synthetic demo database.')
    objects = objects or list(OBJECTS)
    if any(x not in OBJECTS for x in objects):
        raise ValueError('Unsupported CRM object')
    counts = {}
    with connect(db_path) as conn:
        init(conn)
        run_id = conn.execute('INSERT INTO sync_runs(started_at,status) VALUES (?,?)', (_now(),'running')).lastrowid
        conn.commit()
        try:
            for kind in objects:
                count = 0
                for page in client.page_records(kind, OBJECTS[kind]):
                    now = _now()
                    with conn:
                        for record in page:
                            props = record.get('properties') or {}
                            conn.execute('''INSERT INTO crm_records VALUES (?,?,?,?,?,?)
                                ON CONFLICT(object_type,hubspot_id) DO UPDATE SET
                                properties_json=excluded.properties_json, created_at=excluded.created_at,
                                updated_at=excluded.updated_at,last_seen_at=excluded.last_seen_at''',
                                (kind,str(record['id']),json.dumps(props,sort_keys=True),record.get('createdAt'),record.get('updatedAt'),now))
                    count += len(page)
                counts[kind] = count
                conn.execute('INSERT OR REPLACE INTO sync_state VALUES (?,?)', (f'last_success:{kind}',_now()))
                conn.commit()
            if include_associations:
                for from_type, targets in ASSOCIATIONS.items():
                    if from_type not in objects:
                        continue
                    ids = [row[0] for row in conn.execute('SELECT hubspot_id FROM crm_records WHERE object_type=?',(from_type,))]
                    for to_type in targets:
                        if to_type not in objects:
                            continue
                        # Read the complete association response before replacing this edge set.
                        # This also removes stale links when a source now has zero associations.
                        results = list(client.associations(from_type,to_type,ids))
                        with conn:
                            conn.execute('DELETE FROM crm_associations WHERE from_type=? AND to_type=?',(from_type,to_type))
                            for result in results:
                                source_id = str(result['from']['id'])
                                for link in result.get('to',[]):
                                    conn.execute('INSERT OR REPLACE INTO crm_associations VALUES (?,?,?,?,?)', (from_type,source_id,to_type,str(link['toObjectId']),json.dumps(link.get('associationTypes',[]),sort_keys=True)))
            conn.execute('UPDATE sync_runs SET finished_at=?,status=?,counts_json=? WHERE run_id=?',(_now(),'succeeded',json.dumps(counts,sort_keys=True),run_id))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            conn.execute('UPDATE sync_runs SET finished_at=?,status=?,counts_json=?,error=? WHERE run_id=?',(_now(),'failed',json.dumps(counts,sort_keys=True),type(exc).__name__,run_id))
            conn.commit()
            raise
    return counts

def export(db_path='data/hubspot_live.db', out='data/hubspot_exports'):
    """Export a separate, explicitly live-labelled relational dataset."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    counts = {}
    with connect(db_path) as conn:
        for kind, fields in OBJECTS.items():
            rows = conn.execute('SELECT hubspot_id,properties_json FROM crm_records WHERE object_type=? ORDER BY hubspot_id',(kind,)).fetchall()
            with (out/f'{kind}.csv').open('w',newline='',encoding='utf-8') as f:
                writer=csv.DictWriter(f,fieldnames=['hubspot_id']+fields)
                writer.writeheader()
                for identifier,raw in rows:
                    props=json.loads(raw)
                    writer.writerow({'hubspot_id':identifier,**{k:props.get(k) for k in fields}})
            counts[kind]=len(rows)
        with (out/'associations.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f)
            writer.writerow(['from_type','from_id','to_type','to_id','association_types_json'])
            writer.writerows(conn.execute('SELECT * FROM crm_associations ORDER BY from_type,from_id,to_type,to_id'))
    return counts
