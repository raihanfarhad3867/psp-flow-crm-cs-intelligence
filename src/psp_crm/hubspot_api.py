"""HubSpot REST transport. No network call is made at import time.

The default client is read-only. Explicit write permission is required for mutations.
"""
from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlsplit

import requests

API_ROOT = 'https://api.hubapi.com'
RETRYABLE = {429, 500, 502, 503, 504}


class HubSpotError(RuntimeError):
    def __init__(self, status: int, message: str, category: str = ''):
        self.status = status
        self.category = category
        super().__init__(f'HubSpot HTTP {status}: {category}: {message}')


@dataclass
class HubSpotClient:
    token: str | None = None
    session: Any = None
    allow_writes: bool = False
    max_retries: int = 3
    timeout: int = 30
    sleep: Any = time.sleep

    def __post_init__(self):
        self.token = self.token or os.getenv('HUBSPOT_PRIVATE_APP_TOKEN') or os.getenv('HUBSPOT_ACCESS_TOKEN')
        if not self.token:
            raise RuntimeError('Set HUBSPOT_PRIVATE_APP_TOKEN or HUBSPOT_ACCESS_TOKEN in your local environment.')
        self.session = self.session or requests.Session()

    def request(self, method: str, path: str, *, params=None, json=None):
        method = method.upper()
        if not path.startswith('/') or path.startswith('//') or urlsplit(path).scheme or '?' in path:
            raise ValueError('Use an absolute API path without a query string.')
        if method not in {'GET', 'POST', 'PATCH', 'PUT', 'DELETE'}:
            raise ValueError('Unsupported HTTP method')
        if method != 'GET' and not self.allow_writes:
            # Read-only POST endpoints (search and association batch/read) are allowed.
            if not (method == 'POST' and (path.endswith('/search') or path.endswith('/batch/read'))):
                raise PermissionError('CRM mutations are disabled. Explicitly enable writes for an isolated demo account.')
        headers = {'Authorization': f'Bearer {self.token}', 'Accept': 'application/json', 'Content-Type': 'application/json'}
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(method, API_ROOT + path, headers=headers, params=params, json=json, timeout=self.timeout)
            except (requests.Timeout, requests.ConnectionError):
                if attempt == self.max_retries:
                    raise
                self.sleep(min(2 ** attempt, 8))
                continue
            if response.status_code in RETRYABLE and attempt < self.max_retries:
                retry_after = response.headers.get('Retry-After')
                try:
                    delay = max(0.0, min(float(retry_after), 60.0)) if retry_after is not None else min(2 ** attempt, 8)
                except ValueError:
                    delay = min(2 ** attempt, 8)
                self.sleep(delay)
                continue
            if response.status_code >= 400:
                try:
                    body = response.json()
                except ValueError:
                    body = {}
                # Never put response bodies or credentials into errors/logs.
                raise HubSpotError(response.status_code, str(body.get('message', 'Request failed'))[:300], str(body.get('category', '')))
            if response.status_code == 204 or not response.content:
                return {}
            return response.json()
        raise RuntimeError('Unreachable retry state')

    def page_records(self, object_type: str, properties: Iterable[str], *, limit: int = 100):
        """Yield every page, following opaque paging.next.after cursors."""
        if object_type not in {'companies', 'contacts', 'deals', 'tickets', 'tasks'}:
            raise ValueError('Object type is not allowlisted')
        after = None
        seen = set()
        while True:
            params = {'limit': min(max(limit, 1), 100), 'archived': 'false', 'properties': ','.join(properties)}
            if after is not None:
                params['after'] = after
            body = self.request('GET', f'/crm/v3/objects/{object_type}', params=params)
            yield body.get('results', [])
            after = body.get('paging', {}).get('next', {}).get('after')
            if after is None:
                break
            if str(after) in seen:
                raise RuntimeError('HubSpot returned a repeated pagination cursor')
            seen.add(str(after))

    def records(self, object_type: str, properties: Iterable[str]):
        for page in self.page_records(object_type, properties):
            yield from page

    def associations(self, from_type: str, to_type: str, ids: Iterable[str]):
        """Read v4 associations in bounded batches, retaining association labels."""
        allowed = {'companies', 'contacts', 'deals', 'tickets', 'tasks'}
        if from_type not in allowed or to_type not in allowed:
            raise ValueError('Object type is not allowlisted')
        ids = list(dict.fromkeys(str(x) for x in ids))
        for start in range(0, len(ids), 100):
            body = self.request('POST', f'/crm/v4/associations/{from_type}/{to_type}/batch/read', json={'inputs': [{'id': x} for x in ids[start:start + 100]]})
            yield from body.get('results', [])

    def portal(self):
        """Return the portal identity; used to guard demo writes."""
        return self.request('GET', '/integrations/v1/me')

    def upsert_batch(self, object_type: str, records: list[dict], *, id_property: str = 'psp_demo_id'):
        if not self.allow_writes:
            raise PermissionError('Writes disabled')
        if object_type not in {'companies', 'contacts', 'deals'}:
            raise ValueError('Demo writes are restricted to companies, contacts and deals')
        if id_property != 'psp_demo_id':
            raise ValueError('Demo writes must use the dedicated unique identifier')
        results = []
        for start in range(0, len(records), 100):
            inputs = []
            for record in records[start:start + 100]:
                key = str(record['psp_demo_id'])
                if not key.startswith('psp-demo-'):
                    raise ValueError('Only namespaced synthetic records can be written')
                inputs.append({'id': key, 'idProperty': id_property, 'properties': record})
            results.append(self.request('POST', f'/crm/v3/objects/{object_type}/batch/upsert', json={'inputs': inputs}))
        return results
