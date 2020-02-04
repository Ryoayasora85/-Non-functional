#!/bin/sh

function deleteRefFiles(){
  rm  ../envName.txt ../actID.txt ../join.txt
}

function getSwichInfo() {
  #OpeAdmin_各環境リンク一覧.txtから、スイッチロール用のARN生成
  IFS_BACKUP=$IFS
  IFS=$'=,&'
  while read line
  do
    if [[ $line =~ "OpeAdminRole" ]]; then
      echo $line|awk '{print $6}' 1>> ../envName.txt 2> /dev/null
      echo "arn:aws:iam::`echo $line|awk '{print $4}'`:role/OpeAdminRole" 1>> ../actID.txt 2> /dev/null
    fi
  done <../OpeAdmin_各環境リンク一覧.txt
  IFS=$IFS_BACKUP
  # 環境数を行数カウント
  aline=`cat ../actID.txt |wc -l`
  echo "all- All Environments" 1>> ../envName.txt 2> /dev/null
  echo "select all environments" 1>> ../actID.txt 2> /dev/null
  paste -d : ../envName.txt ../actID.txt >../join.txt
  # 選択できる環境を視覚化
  cat ../join.txt |nl -w3 -s"- " -bpINV
}

function ConfirmExecution() {

  xinput=$1

  if [ -z $xinput ] ; then
    echo "何も入力されていません。"
    ConfirmExecution $xinput
    deleteRefFiles
  elif [[ $xinput =~ [0-9]{1} ]] || [[ $xinput =~ [0-9]{2} ]] || [[ $xinput == "all" ]]; then
    echo "スクリプトを実行します。"
  elif [ $xinput = 'no' ] || [ $xinput = 'NO' ] || [ $xinput = 'n' ] ; then
    echo "スクリプトを終了します."
    deleteRefFiles
    exit 1
  else
    echo "番号 または no を入力して下さい."
    ConfirmExecution $xinput
    deleteRefFiles
  fi
}

function swichRoleCmd() {

  count=$1
  shift
  cmdexe=$*

  arnID=`cat ../actID.txt|sed -n ${count}p`
  
  #AWSアカウントID確認
  aws sts get-caller-identity
  if [ $? -ne 0 ]; then
    echo "get-caller-identityに失敗しました。"
    deleteRefFiles
    exit 1
  fi
  
  #assume-role設定
  aws sts assume-role --role-arn $arnID --role-session-name inv-`date "+%Y%m%d%H%M%S"`>>../assume-role.json
  if [ $? -ne 0 ]; then
    echo "スイッチロールに失敗しました。"
    deleteRefFiles
    rm ../assume-role.json
    exit 2
  fi
  
  ackID=`cat ../assume-role.json |jq -r ".Credentials.AccessKeyId"`
  sakID=`cat ../assume-role.json |jq -r ".Credentials.SecretAccessKey"`
  sstID=`cat ../assume-role.json |jq -r ".Credentials.SessionToken"`
  
  export AWS_ACCESS_KEY_ID=$ackID
  export AWS_SECRET_ACCESS_KEY=$sakID
  export AWS_SESSION_TOKEN=$sstID

  #assume-role確認
  aws sts get-caller-identity
  if [ $? -ne 0 ]; then
    echo "get-caller-identityに失敗しました。"
    deleteRefFiles
    rm ../assume-role.json
    exit 3
  fi

  # SwichRole先環境、コマンド実行
  #if [[ $cmdexe =~ ".sh" ]]; then
   # bash $cmdexe
  #else
  #fi

  echo `git remote set-url origin $cmdexe`
  echo $cmdexe
  git remote set-url origin $cmdexe

  git remote -v

  git add .

  git commit -m "`date`"

  sleep 0.5 

  git push origin master

  sleep 3

  rm ../assume-role.json
}

## main

count=$1
shift
cmd=$*

getSwichInfo

ConfirmExecution "$count" 

echo "${cmd}"

swichRoleCmd $count "${cmd}"

echo "スクリプトを終了します"

deleteRefFiles

