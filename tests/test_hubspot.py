import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import json
import sqlite3
import pytest
import requests
from psp_crm.hubspot_api import HubSpotClient, HubSpotError
from psp_crm.hubspot_sync import sync, export

class Response:
    def __init__(self,status=200,body=None,headers=None):
        self.status_code=status;self.body=body or {};self.headers=headers or {};self.content=b'{}'
    def json(self):return self.body

class Session:
    def __init__(self,responses):self.responses=list(responses);self.calls=[]
    def request(self,method,url,**kwargs):
        self.calls.append((method,url,kwargs))
        result=self.responses.pop(0)
        if isinstance(result,Exception):raise result
        return result

def client(responses,**kwargs):
    s=Session(responses)
    return HubSpotClient(token='test-token',session=s,sleep=lambda _:None,**kwargs),s

def test_pagination_and_auth():
    c,s=client([Response(body={'results':[{'id':'1'}],'paging':{'next':{'after':'cursor'}}}),Response(body={'results':[{'id':'2'}]})])
    assert [r['id'] for r in c.records('companies',['name'])]==['1','2']
    assert s.calls[1][2]['params']['after']=='cursor'
    assert s.calls[0][2]['headers']['Authorization']=='Bearer test-token'

def test_retries_rate_limit_and_5xx():
    delays=[]
    c,s=client([Response(429,headers={'Retry-After':'2'}),Response(503),Response(body={'ok':True})])
    c.sleep=delays.append
    assert c.request('GET','/test')=={'ok':True}
    assert delays==[2.0,2]
    assert len(s.calls)==3

def test_auth_error_no_token_leak():
    c,_=client([Response(401,{'message':'Not authorized','category':'INVALID_AUTHENTICATION'})])
    with pytest.raises(HubSpotError) as err:c.request('GET','/test')
    assert err.value.status==401
    assert 'test-token' not in str(err.value)

def test_writes_blocked_by_default():
    c,s=client([])
    with pytest.raises(PermissionError):c.upsert_batch('companies',[{'psp_demo_id':'psp-demo-1'}])
    assert s.calls==[]
    with pytest.raises(PermissionError):c.request('DELETE','/crm/v3/objects/companies/1')

def test_namespaced_upsert_payload_and_batching():
    c,s=client([Response(body={'results':[{'id':'1'}]})],allow_writes=True)
    result=c.upsert_batch('companies',[{'psp_demo_id':'psp-demo-1','name':'Example'}])
    assert result[0]['results'][0]['id']=='1'
    assert s.calls[0][1].endswith('/batch/upsert')
    assert s.calls[0][2]['json']['inputs'][0]['idProperty']=='psp_demo_id'
    with pytest.raises(ValueError):c.upsert_batch('companies',[{'psp_demo_id':'real-1'}])

def test_read_only_association_batching():
    c,s=client([Response(body={'results':[{'from':{'id':'1'},'to':[]}]})])
    assert list(c.associations('contacts','companies',['1']))[0]['from']['id']=='1'
    assert s.calls[0][0]=='POST'
    assert not c.allow_writes

def test_sync_rerun_and_export(tmp_path):
    class Fake:
        def page_records(self,kind,properties):
            yield [{'id':'1','properties':{'name':'Example','email':'x@example.invalid'},'createdAt':'2026-01-01','updatedAt':'2026-01-01'}]
        def associations(self,from_type,to_type,ids):
            yield {'from':{'id':'1'},'to':[{'toObjectId':'1','associationTypes':[{'typeId':1,'category':'HUBSPOT_DEFINED'}]}]}
    db=tmp_path/'live.db'
    assert sync(Fake(),db,['companies','contacts'])=={'companies':1,'contacts':1}
    sync(Fake(),db,['companies','contacts'])
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT COUNT(*) FROM crm_records').fetchone()[0]==2
        assert conn.execute('SELECT COUNT(*) FROM crm_associations').fetchone()[0]==1
        assert conn.execute('SELECT COUNT(*) FROM sync_runs WHERE status="succeeded"').fetchone()[0]==2
    assert export(db,tmp_path/'out')['companies']==1
    assert (tmp_path/'out'/'companies.csv').exists()

def test_sync_failure_is_recorded(tmp_path):
    class Fail:
        def page_records(self,*args):raise RuntimeError('failure')
    db=tmp_path/'fail.db'
    with pytest.raises(RuntimeError):sync(Fail(),db,['companies'])
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT status FROM sync_runs').fetchone()[0]=='failed'


def test_removed_associations_are_reconciled(tmp_path):
    class Fake:
        links = True
        def page_records(self, kind, properties):
            yield [{'id':'1','properties':{'name':'Example'}}]
        def associations(self, from_type, to_type, ids):
            if self.links:
                yield {'from':{'id':'1'},'to':[{'toObjectId':'1','associationTypes':[]}]}
    fake=Fake()
    db=tmp_path/'live.db'
    sync(fake,db,['companies','contacts'])
    fake.links=False
    sync(fake,db,['companies','contacts'])
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT COUNT(*) FROM crm_associations').fetchone()[0]==0


def test_actual_local_http_transport():
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread
    from unittest.mock import patch
    from psp_crm import hubspot_api
    class Handler(BaseHTTPRequestHandler):
        calls=0
        def log_message(self,*args):pass
        def do_GET(self):
            Handler.calls+=1
            assert self.headers['Authorization']=='Bearer test-token'
            if Handler.calls==1:
                self.send_response(429)
                self.send_header('Retry-After','0')
                body=b'{}'
            else:
                self.send_response(200)
                body=json.dumps({'results':[{'id':str(Handler.calls-1)}],**({'paging':{'next':{'after':'next'}}} if Handler.calls==2 else {})}).encode()
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(body)))
            self.end_headers();self.wfile.write(body)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        with patch.object(hubspot_api,'API_ROOT',f'http://127.0.0.1:{server.server_port}'):
            c=HubSpotClient(token='test-token',sleep=lambda _:None)
            assert [r['id'] for r in c.records('companies',['name'])]==['1','2']
        assert Handler.calls==3
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)

def test_verified_snapshot_loader_and_live_dashboard_import(tmp_path):
    import importlib
    module = importlib.import_module('psp_crm.live_dashboard')
    assert hasattr(module, 'render_live')
