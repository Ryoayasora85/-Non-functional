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

## ここからグローバル変数宣言

# リージョン名の取得
roles = boto3.client('sts').get_caller_identity().get('Account')
# 環境変数の取得
ENV = os.environ['ENV']
SER = os.environ['SER']
fileName = os.environ['fileName']
s3Bucket = os.environ['s3Bucket']
s3keyPrefix = os.environ['s3keyPrefix']
slackWebhookUrl = os.environ['LmSlackWebhookUrl']
# monitor.jsonが格納された、S3バケットのパスを生成
filePath = '/tmp/' + fileName

## ログ作成
def logging(logLv, logMsg):
    '''

    ---logging関数---

    監視Lambdaのログの整形を行う。

    '''

    logTimeStump = dt.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    logmess = str(logLv) + " " + str(logTimeStump) + " " + str(logMsg)
    print(logmess)

    return logmess

## 例外処理の通知
def _exception(logmess, lm_info):
    '''

    ---_exception関数---

    例外処理をSlackと、SNSトピック(inv-{env}-{microservice}-notification)に登録されたメールアドレスに送信する。

    ---引数の内容---

    logmess: 各関数(loggingと、_exception以外)から、渡される、例外処理のメッセージ内容
    lm_info: contextから取得した、監視Lambdaのデータ

    '''
    # 通知用のヘッダ
    description = "監視Lambdaにて、エラーが発生しました。"
    # 通知用URLの生成
    log_url = "https://"+str(lm_info[2])+".console.aws.amazon.com/cloudwatch/home?region="+str(lm_info[2])+"#logEventViewer:group="+str(lm_info[0])+";stream="+str(lm_info[1])
    # SNSトピックARNの生成
    MailArn="arn:aws:sns:ap-northeast-1:" + str(roles) + ":inv-" + str(ENV) + "-" + str(SER) + "-notification"
    # 通知先指定contactの生成
    contact = {'SLACK':slackWebhookUrl, 'Mail':MailArn}
    title = "【inv-" + str(ENV) + "-" + str(SER) + "】-" + "監視Lambdaエラー通知"
    logging("INFO", "Post notification to Slack : %s" %title)
    post_slack(lm_info, logmess, log_url, contact, description)
    logging("INFO", "Post notification to Mail : %s" %title)
    post_sns(lm_info, logmess, log_url, contact, description, title)
    return

## S3から、monitor.jsonファイルを取得
def getS3List(lm_info, fileName, s3keyPrefix, s3Bucket, filePath):
    '''

    ---getS3List関数---

    S3から設定ファイル(monitor.json)を取得する。

    '''

    try:
        s3 = boto3.resource('s3')
        newFileName = s3keyPrefix + fileName

        s3.Bucket(s3Bucket).download_file(newFileName, filePath)
        with open(filePath) as f:
            lines = json.load(f)
            return lines
    except Exception as e:
        logmess = logging("ERROR", "Fail to get files from S3-backet : %s" % str(e))
        _exception(logmess, lm_info)
        sys.exit()

## slack通知
def post_slack(lm_info, log_data, log_url, contact, description):
    '''

    ---post_slack関数---

    Slackに通知内容を送信する。

    '''

    try:
        SLACK_POST_URL = contact['SLACK']
        channel = os.environ['LmSlackChannel']
        
        message = str(description) + \
            "\n" + str(log_data) + \
            "\n" + log_url
        
        params = {
            'channel':channel,
            'text': message
        }
        # requestsモジュールで、SlackにPOST
        requests.post(SLACK_POST_URL, data=json.dumps(params))
    except Exception as e:
        logmess = logging("ERROR", "Fail to post slack : %s" % str(e))
        _exception(logmess, lm_info)
        sys.exit()

## Mail通知
def post_sns(lm_info, log_data, log_url, contact, description, title):
    '''

    --post_sns関数--

    SNSトピックに登録されたメールアドレスに通知内容を送信する。

    '''

    try:
        topic_arn = contact['Mail']
        sns = boto3.client('sns')

        sns_message = description + \
            "\n" + log_data+ \
            "\n" + log_url


        responses = sns.publish(
            TopicArn = topic_arn,
            Message = sns_message,
            Subject = title
        )
    except Exception as e:
        logmess = logging("ERROR", "Fail to post Mail : %s" % str(e))
        _exception(logmess, lm_info)
        sys.exit()

## 通知先判定
def judge_nortify(lm_info, log_data, log_url, x, title):
    '''

    ---judge_nortify関数---

    監視対象の通知先を、設定ファイルのcontactで判別する。

    ---引数の内容---

    x: judge_json関数で、monitor.jsonのvalueだけを格納したデータ
    title: judge_json関数で、通知用に生成した、タイトル

    '''

    try:
        errorcode = x['errorcode']
        contact = x['contact']
        description = x['description']

        # ログ本文に、errorcodeは含まれるか
        if errorcode in log_data:
            # monitor.jsonの、通知指定は、Slackだけか
            if "Mail" not in contact:
                post_slack(lm_info, log_data, log_url, contact, description)
                logging("INFO", "Post notification to Slack : %s" %title)
            # Mailだけか
            elif "SLACK" not in contact:
                post_sns(lm_info, log_data, log_url, contact, description, title)
                logging("INFO", "Post notification to Mail : %s" %title)
            # Slackと、Mail両方の指定か
            else:
                post_slack(lm_info, log_data, log_url, contact, description)
                logging("INFO", "Post notification to Slack : %s" %title)
                post_sns(lm_info, log_data, log_url, contact, description, title)
                logging("INFO", "Post notification to Mail : %s" %title)
        else:
            pass
    except Exception as e:
        logmess = logging("ERROR", "An error occurred. During function judge_nortify processing : %s" % str(e))
        _exception(logmess, lm_info)
        sys.exit()

## 監視対象判定
def judge_json(lm_info, log_data, log_url, spl_logdata, result):
    '''

    ---judge_json関数---

    設定ファイル(monitor.json)のキーやバリューと、ログやイベントデータの中に含まれる文字列と比較
    監視対象を判別する

    ---引数の内容---

    log_data: ログ本文
    spl_logdata: get_log_mess関数で、ログ本文を分割したリスト配列

    '''

    try:
        # monitor.json  読み込み
        listJson = getS3List(lm_info, fileName, s3keyPrefix, s3Bucket, filePath)
        # listJsonのkey,value分、ループ
        for k, v in listJson.items():
            # key毎に、value分ループ
            for x in v:
                # キーがApplication(プログラム監視)か
                if "Application" in k:
                    # spl_logdata内に、errorcodeは完全一致するか
                    if any(s.endswith(x.get('errorcode')) for s in spl_logdata):
                        title = "【inv-" + str(ENV) + "-" + str(SER) + "】-" + "プログラムエラー通知-" + str(x.get('errorcode'))
                        judge_nortify(lm_info, log_data, log_url, x, title)
                # キーがerrorcode_bash(バッシュ内部エラー)か
                elif "errorcode_bash" in k:
                    # spl_logdataの配列の末尾に、errorcodeが含まれるか
                    if x['errorcode'] == spl_logdata[-1]:
                        errorcode = x['errorcode']
                        title = "bash内部エラー通知-" + str(errorcode)
                        judge_nortify(lm_info, log_data, log_url, x, title)
                            # キーがMetrics(メトリクス監視)か
                elif "Metrics" in k:
                    # ログ本文に、ALARMは入っているか
                    if x['StateValue'] in log_data:
                        description = ""
                        contact = x['contact']
                        title = "【inv-" + str(ENV) + "-" + str(SER) + "】-" + "メトリクスアラーム通知"
                        logging("INFO", "Post notification to Slack : %s" %title)
                        post_slack(lm_info, log_data, log_url, contact, description)
                        logging("INFO", "Post notification to Mail : %s" %title)
                        post_sns(lm_info, log_data, log_url, contact, description, title)
                # キーが、ログのURL連番(シナリオ監視)と完全一致するか
                elif k == spl_logdata[3] and x['monitor'] == "scenario":
                    if x['errorcode'] == spl_logdata[-1]:
                        errorcode = x['errorcode']
                        title = str(result) + "-" + "シナリオ検知エラー通知-" + str(errorcode)
                        judge_nortify(lm_info, log_data, log_url, x, title)
                # キーにsummaryか
                elif "summary" in k:
                    if x['errorcode'] == spl_logdata[-1]:
                        errorcode = x['errorcode']
                        title = str(result) + "-" + "シナリオ検知エラー通知-" + str(errorcode)
                        judge_nortify(lm_info, log_data, log_url, x, title)
                else:
                    pass
    except Exception as e:
        logmess = logging("ERROR", "An error occurred. During function judge_json processing : %s" % str(e))
        _exception(logmess, lm_info)
        sys.exit()

## ログの整形
def get_log_mess(log_json, lm_info, log_url):
    '''

    ---get_log_mess関数---

    CLoudWatch Logsから取得したパラメータを選別。

    ---引数の内容---

    log_json: lambda_handlerのevent（プログラム監視、あるいはシナリオ監視起因）のログデータ
    lm_info: lambda_handlerのcontextから取得した、Lambdaのパラメータをリスト配列に格納したデータ

    '''

    try:
              # log_jsonのパラメータのうちlogEventsだけ、ループしてkey, valuesに分割
        log_spl = [v for k, v in log_json.items() if k == 'logEvents']
        # log_splの二重カッコ[[]]を外し、パラメータの中からmessageだけを配列に格納
        log_mess = [v for lst in log_spl for sec_lst in lst for k, v in sec_lst.items() if k == 'message']
        for log_data in log_mess:
            # 空白行で、分割し配列に格納
            spl_log = log_data.split()
            # コロンで、分割し配列に格納
            spl_data = [y for x in spl_log for y in x.split(':')]
            # リストの要素数エラーを防ぐために、同じ配列を結合
            spl_logdata = spl_data + spl_data
            spl_result = spl_log[0]
            # シナリオ名の値を代入
            result = spl_result[6:]
            judge_json(lm_info, log_data, log_url, spl_logdata, result)
    except Exception as e:
        logmess = logging("ERROR", "An error occurred. During function get_log_mess processing : %s" % str(e))
        _exception(logmess, lm_info)
        sys.exit()

## メイン処理
def lambda_handler(event, context):
    '''

    ---lambda_handler関数---

    メイン処理。
    トリガー（CloudWatch アラーム起因か、ログの検知文字列起因）かを判断し、制御を行う。

    ---引数の内容---
    公式ドキュメント参照

    '''

    try:
        # contextから、url生成のために、監視Lambdaのパラメータを変数に格納
        lm_log_grpname = context.log_group_name
        lm_log_stream = context.log_stream_name
        region = context.invoked_function_arn.split(":")[3]
        lm_info = [lm_log_grpname, lm_log_stream, region]
        # eventの内容が、CloudWatch Logsのイベントデータでないか
        if 'awslogs' not in event:
            # EventSourceに、aws:snsが含まれているか
            if "aws:sns" in event['Records'][0]['EventSource']:
                message_unicode = (event['Records'][0]['Sns']['Message'])
                message_dist = json.loads(message_unicode)
                # アラーム名を、通知用URL用に、URLエンコード
                url_quote = urllib.parse.quote(message_dist['AlarmName'], safe='')
                # Json整形
                msg = json.dumps(message_dist, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
                # 通知用URL生成
                log_url = "https://"+str(region)+".console.aws.amazon.com/cloudwatch/home?region="+str(region)+"#alarmsV2:alarm/"+str(url_quote)
                judge_json(lm_info, msg, log_url, spl_logdata=['M','e','t','r','i','c','s'], result="")
                # 監視lambdaの終了ログ
                logging("INFO", "Lambda-Notification is finished")
        else:
            # CloudWatch Logsのイベントデータを解凍して、デコード
            data_json = json.loads(zlib.decompress(base64.b64decode(event['awslogs']['data']), 16+zlib.MAX_WBITS))
            # Jsonデータを、辞書型にエンコード
            log_json = json.loads(json.dumps(data_json, ensure_ascii=False))
            log_grpname = log_json["logGroup"]
            log_stream = log_json["logStream"]
            # 通知用URLの生成
            log_url = "https://"+str(region)+".console.aws.amazon.com/cloudwatch/home?region="+str(region)+"#logEventViewer:group="+str(log_grpname)+";stream="+str(log_stream)
            get_log_mess(log_json, lm_info, log_url)
            logging("INFO", "Lambda-Notification is finished")
    except Exception as e:
        logmess = logging("ERROR", "An error occurred. During function lambda_handler processing : %s" % str(e))
        _exception(logmess, lm_info)
        sys.exit()


