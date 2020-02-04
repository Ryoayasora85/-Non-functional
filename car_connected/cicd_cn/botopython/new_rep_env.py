#!/usr/bin/env python
# coding: UTF-8

import json
import boto3
import pprint
import codecs
from datetime import date, datetime, timedelta


path = '../OpeAdmin_各環境リンク一覧.txt'

with open(path, 'r') as f:
    l_strip = [s.strip() for s in f.readlines()]

with open('../tmp/monitor.json', 'r') as g:
    df = json.loads(g.read(),'utf-8')

before_ft_env="buzz1"
before_env="inv-hog-hoge1"
before_act_id="fugafugafuga"

for index, x in enumerate(l_strip):
    lenstr=[i for i in x]
    if (index % 2) == 0 and "#" not in lenstr[0]:
        first_env=x[-5:]
        env_name=x[-13:].lower()
        account_id=x[-38:-26]

        print(first_env, env_name, account_id)
        for y, z in df.items():
            if before_ft_env in y:
                rep_y=y.replace(before_ft_env, first_env)
                df[rep_y]=df.pop(y)
            for a in z:
                if before_ft_env in a['description']:
                    rep_a=a['description'].replace(before_ft_env, first_env)
                    a['description']=rep_a
                new_a=a['contact']
                for b, c in new_a.items():
                    if "Mail" in b:
                        if before_env in c:
                            rep_c=c.replace(before_env, env_name)
                            new_c=rep_c.replace(before_act_id, account_id)
                            new_a['Mail']=new_c
        before_ft_env=first_env
        before_env=env_name
        before_act_id=account_id

        path_w = './%s-cfn.json' % env_name.lower()
        with codecs.open(path_w, 'w', 'utf-8') as h:
            dump=json.dumps(df, ensure_ascii=False, indent=4)
            h.write(dump)

