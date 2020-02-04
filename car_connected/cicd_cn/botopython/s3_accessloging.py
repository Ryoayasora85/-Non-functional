#!/usr/bin/env python
# coding: UTF-8

# S3の設計書用の設定情報取得lambda
# bucketごとに情報を設定する

import json
import boto3
from datetime import date, datetime, timedelta

# 日付タイプの変換
def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        # 時差の修正9時間
        obj = obj - timedelta(hours=-9)
        return obj.strftime('%Y/%m/%d %H:%M')
    raise TypeError("Type %s not serializable" % type(obj))

client = boto3.client('s3')
#設定情報を取得するバケットリストを取得
buckets = client.list_buckets()

# 設定情報を代入するjson
json_buckets_setting = {}
json_buckets_setting['Owner'] = buckets['Owner']
json_buckets_setting['Buckets'] = []

for bucket in buckets['Buckets']:
    setting_info = {}

    # 引数が全てBucketなのでevalでメソッドを実行する
    client_methods = [
#        'get_bucket_accelerate_configuration', 'get_bucket_acl', 'get_bucket_cors', 'get_bucket_encryption', 'get_bucket_lifecycle_configuration', 'get_bucket_location', 'get_bucket_logging', 'get_bucket_notification_configuration', 'get_bucket_policy_status', 'get_bucket_request_payment', 'get_bucket_tagging', 'get_bucket_versioning', 'get_bucket_website', 'get_object_lock_configuration', 'get_public_access_block', 'list_bucket_analytics_configurations', 'list_bucket_inventory_configurations', 'list_bucket_metrics_configurations'
        'get_bucket_logging'
    ]
    for method_name in client_methods:
        response = None
        try:
            response = eval("client." + method_name)(
                Bucket=bucket['Name']
            )
        except:
            pass
        setting_info[method_name] = response

    #メソッド毎に設定値を代入
    bucket["s3_setting"] = setting_info
    json_buckets_setting['Buckets'].append(bucket)

#bbbbb=json.loads(json_buckets_setting)
#aaaaa=json.dumps(json_buckets_setting, default=json_serial)
#aaaaa=json.dumps(bbbbb, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
aaaaa=json.dumps(json_buckets_setting, default=json_serial, ensure_ascii=False, indent=4)

print(aaaaa)
