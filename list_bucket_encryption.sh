#!/bin/bash 

exec 2>&- # close standard error

printf "$(aws s3api list-buckets --query "Buckets[].Name")\n" |
while read line
do
    [[ $line =~ \"(.+)\" ]];
    if [[ ! -z  ${BASH_REMATCH[1]} ]]; then
        bucket=${BASH_REMATCH[1]}
        output=$(aws s3api get-bucket-encryption --bucket "${bucket}") 
        if (( $? > 0 )); then
            echo "${bucket}"
        else 
            if [ ! $(echo ${output} | grep -q "aws:kms") ]; then
                echo -n "${bucket} "
                printf "%s" ${output}
                echo 
            fi
        fi
    fi
done