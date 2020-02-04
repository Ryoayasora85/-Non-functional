#!/bin/sh

<< COMMENTOUT
count=$1
shift
cmdx=$*
COMMENTOUT

#for x in `seq 1 $count`; do bash ./all_sw_qer.sh $x "$cmdx"; done
#for x in `seq 1 $count`; do bash ./elb_get_info_4_log.sh $x "$cmdx"; done
#for x in `seq 1 $count`; do bash ./stack_temp_list.sh $x "$cmdx"; done
#for x in `seq 1 $count`; do bash ./s3_list.sh $x "$cmdx"; done
#for x in `seq 1 $count`; do bash ./s3_get_backet_logging.sh $x "$cmdx"; done
#for x in `seq 1 $count`; do bash ./s3_cp.sh $x "$cmdx"; done
#for x in `seq 1 $count`; do bash ./cfn_deploy.sh $x "$cmdx"; done
#for x in `seq 1 $count`; do bash ./cfn_delete.sh $x "$cmdx"; done

#<< COMMENTOUT
cd pipeline_cfn 
count=1
while read line
do
  if  [ $count = 13 ]; then
    break
  else
    bash ../cfn_deploy.sh $count $line
    $((++count)) 
  fi
done <../gitremote.txt
cd ../
#COMMENTOUT
