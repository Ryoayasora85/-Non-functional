#!/bin/bash
 
# リージョン
export AWS_DEFAULT_REGION=ap-northeast-1
 
# CloudWatchLogs設定
LogGroupName="/ecs/logs/test-jmeter-scenario-monitoring-ecs-group"
#LogGroupName="/ecs/logs/inv-aws-scenario-monitoring"
#LogGroupName="/aws/lambda/inv-ver-cer01-manage-metrics-alarm-lambda"
LogStreamName="jmeter-scenario001/jmeter-scenario001/a3d82924-a6fc-4c9b-9d7c-0bcb097f777a"
#LogStreamName="monitoring-lambda-dummy/inv-aws-program-monitoring/2019-06-19-02-12"
 
# CloudWatchLogsにPUTするメッセージ
Mess=$1
 
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
