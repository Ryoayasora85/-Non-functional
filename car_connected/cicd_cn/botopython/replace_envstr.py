#!/usr/bin/env python
# coding: UTF-8

import json
import boto3
import pprint
from datetime import date, datetime, timedelta


path = '../OpeAdmin_各環境リンク一覧.txt'

with open(path) as f:
    l_strip = [s.strip() for s in f.readlines()]

for index, x in enumerate(l_strip):
    if (index % 2) == 0:
        first_env=x[-5:]
        env_name=x[-13:]
        account_id=x[-38:-26]
    else:
      pass

with open('../tmp/monitor.json') as g:
    df = json.load(g)

for y, z in df.items():    
    if "cer01" in y:
        rep_y=y.replace('cer01', 'sub01')
        df[rep_y]=df[y]
        del[y]

    for a in z:
        if "cer01" in a['description']:
            rep_a=a['description'].replace('cer01', 'sub01')    
            a['description']=rep_a
        new_a=a['contact']
        for b, c in new_a.items():
            if "Mail" in b:
                if "inv-prd-com01" in c:
                    rep_c=c.replace('inv-prd-com01', 'inv-ver-sub01')
                    new_c=rep_c.replace('649551049546', '495152581087')
                    new_a['Mail']=new_c

#print(df.keys())
#pprint.pprint(df, width=40)
