#!/bin/sh

function ConfirmExecution() {

  #OpeAdmin_各環境リンク一覧.txtから、スイッチロール用のARN生成
  IFS_BACKUP=$IFS
  IFS=$'=,&'
  while read line
  do
    if [[ $line =~ "OpeAdminRole" ]]; then
      echo $line|awk '{print $6}' 1>> ./envName.txt 2> /dev/null
      echo "arn:aws:iam::`echo $line|awk '{print $4}'`:role/OpeAdminRole" 1>> ./actID.txt 2> /dev/null
    fi
  done <OpeAdmin_各環境リンク一覧.txt
  IFS=$IFS_BACKUP
  paste -d : ./envName.txt ./actID.txt >./join.txt
  cat -n ./join.txt
  read -p "環境（番号）を選択してください。(抜ける場合は"no"を入力) ==>" input

  if [ -z $input ] ; then
    echo "何も入力されていません。"
    ConfirmExecution
    rm  ./envName.txt ./actID.txt ./envName.txt
  elif [[ $input =~ [0-9]{1} ]] || [[ $input =~ [0-9]{2} ]]; then
    echo "スクリプトを実行します。"
  elif [ $input = 'no' ] || [ $input = 'NO' ] || [ $input = 'n' ] ; then
    echo "スクリプトを終了します."
    rm  ./envName.txt ./actID.txt ./envName.txt
    exit 1
  else
    echo "番号 または no を入力して下さい."
    ConfirmExecution
    rm  ./envName.txt ./actID.txt ./envName.txt
  fi

}

function swichRoleCmd() {
  arnID=`cat ./actID.txt|sed -n ${input}p`
  
  #AWSアカウントID確認
  aws sts get-caller-identity
  if [ $? -ne 0 ]; then
    echo "get-caller-identityに失敗しました。"
    exit 1
  fi
  
  #assume-role設定
  aws sts assume-role --role-arn $arnID --role-session-name inv-`date "+%Y%m%d%H%M%S"`>>./assume-role.json
  if [ $? -ne 0 ]; then
    echo "スイッチロールに失敗しました。"
    exit 2
  fi
  
  ackID=`cat assume-role.json |jq -r ".Credentials.AccessKeyId"`
  sakID=`cat assume-role.json |jq -r ".Credentials.SecretAccessKey"`
  sstID=`cat assume-role.json |jq -r ".Credentials.SessionToken"`
  
  export AWS_ACCESS_KEY_ID=$ackID
  export AWS_SECRET_ACCESS_KEY=$sakID
  export AWS_SESSION_TOKEN=$sstID
  
  aws sts get-caller-identity
  if [ $? -ne 0 ]; then
    echo "get-caller-identityに失敗しました。"
    exit 3
  fi
  
  read -p "実行したいコマンド、またはスクリプトを指定してください。 ==>" cmd
  if [[ $cmd =~ ".sh" ]]; then
    bash $cmd
  else
    $cmd
  fi
  
  echo "スクリプトを終了します"
  rm  ./envName.txt ./actID.txt ./join.txt ./assume-role.json
}

## main
ConfirmExecution
swichRoleCmd ${input}
