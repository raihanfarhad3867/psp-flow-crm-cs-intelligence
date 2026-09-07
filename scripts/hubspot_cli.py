"""Read-only live HubSpot connector CLI."""
from pathlib import Path
import argparse
import json
import os
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / '.env')
from psp_crm.hubspot_api import HubSpotClient
from psp_crm.hubspot_sync import OBJECTS, sync, export


def main():
    p=argparse.ArgumentParser(description='HubSpot integration. Live data stays separate from the synthetic demo.')
    p.add_argument('command',choices=['check','sync','export'])
    p.add_argument('--db',default='data/hubspot_live.db')
    p.add_argument('--out',default='data/hubspot_exports')
    p.add_argument('--objects',nargs='+',choices=list(OBJECTS))
    args=p.parse_args()
    if args.command=='export':
        print(json.dumps(export(args.db,args.out),indent=2)); return
    client=HubSpotClient()
    if args.command=='check':
        # A single harmless API read confirms access to the account's company object.
        page=next(client.page_records('companies',['name'],limit=1))
        print(json.dumps({'authenticated_read':True,'object':'companies','sample_count':len(page),'mode':'read-only'},indent=2));return
    counts=sync(client,args.db,args.objects)
    print(json.dumps({'mode':'read-only','counts':counts,'database':args.db},indent=2))

if __name__=='__main__':
    main()
