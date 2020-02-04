#!/bin/bash

# リージョン
export AWS_DEFAULT_REGION=ap-northeast-1

# CloudWatchLogs設定
LogGroupName="/monitoring-lambda-dummy"

LogStreamName="test20190716"

# CloudWatchLogsにPUTするメッセージ
Mess="LogLevel:ERROR Uuid:7a33d6d6-878f-4f1d-bc80-f1e09dbcc4cc Time:2019/04/10 13:33:51.299+09:00 Env:DEV Service:wfi Pgm:jp.ne.internavi.cloud.wifi.common.handler.GlobalExceptionHandler.restClientExceptionHandler(GlobalExceptionHandler.java:172) RecId:777777777 Message:wfi log X-AppVer:0.0.7 Y-ErrorId:FATAL-001 X-IccId: X-ExceptionMsg:I/O error on POST request for "/localhost/api/get_iccid": null; nested exception is org.apache.http.client.ClientProtocolException X-Exception:org.springframework.web.client.ResourceAccessException X-DetailedValue:An external error occurred"

# コーテーションを取り除く
Mess=`echo $Mess | sed -e "s/'//g"`

# put-log-eventに利用するトークン
UploadSequenceToken=$(aws logs describe-log-streams --log-group-name "$LogGroupName" --query 'logStreams[?logStreamName==`'$LogStreamName'`].[uploadSequenceToken]' --output text)

# put-log-eventに利用するタイムスタンプ
TimeStamp=`date "+%s%N" --utc`
TimeStamp=`expr $TimeStamp / 1000000`

# put-log-eventsの実行
if [ "$UploadSequenceToken" != "None" ]
then
  # トークン有りの場合
  aws logs put-log-events --log-group-name "$LogGroupName" --log-stream-name "$LogStreamName" --log-events timestamp=$TimeStamp,message="$Mess" --sequence-token $UploadSequenceToken
else
  # トークン無しの場合（初回のput）
  aws logs put-log-events --log-group-name "$LogGroupName" --log-stream-name "$LogStreamName" --log-events timestamp=$TimeStamp,message="$Mess"
fi
