#!/bin/sh

function Rds_Update_Execution() {

    rds_arg=$1

    while read line
    do
        echo "「`echo $line`」のRDSの証明書を更新します。"
        if [[ $line =~ "zocalo" ]] || [[ $line =~ "stecky" ]]; then
            aws rds modify-db-instance --db-instance-identifier $line --ca-certificate-identifier rds-ca-2019 --license-model license-included --apply-immediately --profile prod
            if [ $? -ne 0 ]; then
                echo "`echo $line`証明書の更新に失敗しました。"
                exit 0
            fi
        elif [[ $line =~ "ddex-db11" ]]; then
            aws rds modify-db-instance --db-instance-identifier $line --ca-certificate-identifier rds-ca-2019 --cloudwatch-logs-export-configuration EnableLogTypes=general,error,audit,slowquery --apply-immediately --profile prod
            if [ $? -ne 0 ]; then
                echo "`echo $line`証明書の更新に失敗しました。"
                exit 1
            fi
        else
            aws rds modify-db-instance --db-instance-identifier $line --ca-certificate-identifier rds-ca-2019 --apply-immediately --profile prod
            if [ $? -ne 0 ]; then
                echo "`echo $line`証明書の更新に失敗しました。"
                exit 2
            fi
        fi
        echo "「`echo $line`」の証明書を更新しました。"
    done <./$rds_arg
}

## メイン

# テキストデータの指定
args=$1

# 入力処理
echo "次のテキストを読み込みます。 => `echo $args`"
echo "----- 以下は `echo $args`　の内容です。確認してください。　-----"
cat ./$args
echo "------------------------------------------------------------"
read -p "スクリプトを実行してよろしいですか？(Y/N) : " input
case $input in
  "" | [Yy]* )
    echo "Yesが入力されました。RDS更新作業を実施します。"
    Rds_Update_Execution $args
    ;;
  * )
    echo "Noが入力されました。スクリプトを終了します。"
    ;;
esac

echo "スクリプトを終了しました。"

