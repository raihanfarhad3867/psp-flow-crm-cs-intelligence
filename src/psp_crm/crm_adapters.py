"""Compatibility adapters for the original local CRM demo."""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable
from .hubspot_api import HubSpotClient

@dataclass
class SyncResult:
    object_name: str
    attempted: int
    succeeded: int
    failed: int
    mode: str
    message: str

class LocalCRMAdapter:
    mode = 'local-fallback'
    def upsert(self, object_name: str, records: Iterable[Dict[str, Any]], key: str) -> SyncResult:
        records = list(records)
        seen = {r.get(key) for r in records}
        return SyncResult(object_name, len(records), len(seen), len(records)-len(seen), self.mode, f'Local deduplication using {key}.')

class HubSpotAdapter(HubSpotClient):
    mode = 'hubspot-api'
    def upsert(self, object_name: str, records: Iterable[Dict[str, Any]], key: str = 'psp_demo_id') -> SyncResult:
        records = list(records)
        responses = self.upsert_batch(object_name, records, id_property=key)
        succeeded = sum(len(r.get('results', [])) for r in responses)
        return SyncResult(object_name, len(records), succeeded, len(records)-succeeded, self.mode, 'HubSpot API batch upsert completed.')

def get_adapter():
    return HubSpotAdapter() if (os.getenv('HUBSPOT_PRIVATE_APP_TOKEN') or os.getenv('HUBSPOT_ACCESS_TOKEN')) else LocalCRMAdapter()
