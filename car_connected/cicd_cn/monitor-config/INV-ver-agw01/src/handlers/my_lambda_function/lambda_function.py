import os
import sys
import json
import boto3
import zlib
import base64
import datetime
from datetime import datetime as dt
import urllib
import requests

print('loading function')
    
## Create Logs
def logging(logLv, logMsg):

    logTimeStump = dt.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    print(str(logLv) + " " + str(logTimeStump) + " " + str(logMsg))
    return

## S3 get list
def getList(fileName, s3keyPrefix, s3Bucket, filePath):

    s3 = boto3.resource('s3')
    
    newFileName = s3keyPrefix + fileName

    try:
        s3.Bucket(s3Bucket).download_file(newFileName, filePath)
        with open(filePath) as f:
            lines = json.load(f)
            return lines
    except Exception:
        logging("ERROR", "Fail to get files from S3-backet")
        sys.exit()

## post slack
def post_slack(log_data, log_url, contact, description):

    SLACK_POST_URL = contact['SLACK']
    channnel = '#connectcommon'

    message = str(description) + \
        "\n" + str(log_data) + \
        "\n" + log_url

    params = {
        'channel':channnel,
        'text': message
    }
    try:
        r = requests.post(SLACK_POST_URL, data=json.dumps(params))
    except Exception:
        logging("ERROR", "Fail to post slack")
        sys.exit()

## post mail
def post_sns(log_data, log_url, contact, description, title):

    topic_arn = contact['Mail']
    sns = boto3.client('sns')

    sns_message = description + \
        "\n" + log_data+ \
        "\n" + log_url

    try:
        responses = sns.publish(
            TopicArn = topic_arn,
            Message = sns_message,
            Subject = title
        )
    except Exception:
        logging("ERROR", "Fail to post Mail")
        sys.exit()

# judg_status
def judge_status(log_data, log_url, x, title):

    errorcode = x['errorcode']
    contact = x['contact']
    description = x['description']

    if errorcode in log_data:
        print("true")
        if "Mail" not in contact:
            post_slack(log_data, log_url, contact, description)
            logging("INFO", "Post Slack")
        elif "SLACK" not in contact:
            post_sns(log_data, log_url, contact, description, title)
            logging("INFO", "Post Mail")
        else:
            post_slack(log_data, log_url, contact, description)
            logging("INFO", "Post Slack")
            post_sns(log_data, log_url, contact, description, title)
            logging("INFO", "Post Mail")
    else:
        print("false")

## main
def lambda_handler(event, context):
    # global val
    ENV = os.environ['ENV']
    STG = os.environ['STG']
    # s3 param
    fileName = os.environ['fileName']
    s3Bucket = os.environ['s3Bucket']
    s3keyPrefix = os.environ['s3keyPrefix']
    filePath = '/tmp/' + fileName
    region = context.invoked_function_arn.split(":")[3]

    # get logs
    if 'awslogs' not in event:
        if "aws:sns" in event['Records'][0]['EventSource']:
            message_unicode = (event['Records'][0]['Sns']['Message'])
            message_dist = json.loads(message_unicode)
            url_quote = urllib.parse.quote(message_dist['AlarmName'], safe='')
            msg = json.dumps(message_dist, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
            log_url = "https://"+str(region)+".console.aws.amazon.com/cloudwatch/home?region="+str(region)+"#alarmsV2:alarm/"+str(url_quote)
            # read list and push notification
            listJson = getList(fileName, s3keyPrefix, s3Bucket, filePath)
            for k, v in listJson.items():
                for x in v:
                    if "Metrics" in k:
                        description = ""
                        contact = x['contact']
                        title = "【inv-" + str(STG) + "-" + str(ENV) + "】-" + "メトリクスアラーム通知"
                        post_slack(msg, log_url, contact, description)
                        post_sns(msg, log_url, contact, description, title)
    else:
        data_json = json.loads(zlib.decompress(base64.b64decode(event['awslogs']['data']), 16+zlib.MAX_WBITS))
        log_json = json.loads(json.dumps(data_json, ensure_ascii=False))
        log_grpname = log_json["logGroup"]
        log_stream = log_json["logStream"]

        # log stream url
        log_url = "https://"+str(region)+".console.aws.amazon.com/cloudwatch/home?region="+str(region)+"#logEventViewer:group="+str(log_grpname)+";stream="+str(log_stream)

        # read list and push notification
        listJson = getList(fileName, s3keyPrefix, s3Bucket, filePath)

        for mess in log_json['logEvents']:
            log_data = mess['message']
            spl_logdata = log_data.split()
            spl_result = spl_logdata[0]
            result = spl_result[6:]
            for sepmes in spl_logdata:
                if 'X-ErrorId' in sepmes:
                    spl_sm = sepmes.split(':')
                    ssm = spl_sm[1]
            for k, v in listJson.items():
                for x in v:
                    if "Application" in k:
                        if 'ssm' in locals():
                            if ssm == x.get('errorcode'):
                                title = "【inv-" + str(ENV) + "-" + str(STG) + "】-" + "プログラムエラー通知-" + str(ssm)
                                judge_status(log_data, log_url, x, title)
                    elif "errorcode_bash" in k:
                        if x['errorcode'] in log_data:
                            errorcode = x['errorcode']
                            title = "bash内部エラー通知-" + str(errorcode)
                            judge_status(log_data, log_url, x, title)
                    else :
                        if x['errorcode'] in log_data:
                            errorcode = x['errorcode']
                            title = str(result) + "-" + "シナリオ検知エラー通知-" + str(errorcode)
                            judge_status(log_data, log_url, x, title)


