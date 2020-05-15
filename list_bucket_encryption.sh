#!/bin/bash 

exec 2>&- # close standard error

printf "$(aws s3api list-buckets --query "Buckets[].Name")\n" |
while read line
do
    [[ $line =~ \"(.+)\" ]];
    if [[ ! -z  ${BASH_REMATCH[1]} ]]; then
        bucket=${BASH_REMATCH[1]}
        echo $bucket
        echo -ne "\t"
        echo $(aws s3api get-bucket-encryption --bucket "${bucket}") 2>/dev/null
    fi
done