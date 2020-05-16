#!/usr/bin/env python
import logging
import boto3
import sys, argparse
import yaml
import asyncio
from botocore.exceptions import ClientError


async def retrieveSecurityPolicy(s3, buckets, bucket):
    try:
        # Get each buck name encryption
        response = s3.get_bucket_encryption(
            Bucket=bucket
        )

        # Print indicator when a bucket has response
        print("." , end="", flush=True)

        # When a encyption info is found save to dictionary 
        if "ServerSideEncryptionConfiguration" in response and "Rules" in response["ServerSideEncryptionConfiguration"] and len(response["ServerSideEncryptionConfiguration"]["Rules"]) > 0:
            for rule in response["ServerSideEncryptionConfiguration"]["Rules"]:
               if "ApplyServerSideEncryptionByDefault" in rule and "SSEAlgorithm" in rule["ApplyServerSideEncryptionByDefault"]:
                    if rule["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"] == "aws:kms":
                        del buckets[bucket]
                    else: 
                        buckets[bucket] = response["ServerSideEncryptionConfiguration"]

    except ClientError:
        pass
        # print('Bucket %s has no bucket encryption configured' % bucket) 


# Main Program
async def main():

    # Argument parser
    parser = argparse.ArgumentParser(description='List and audit S3 Encryption buckets and save ServerSideEncryptionConfiguration.', 
                                     argument_default=argparse.SUPPRESS)

    parser.add_argument('--save', metavar='file',
                        default='audit.yml', 
                        help='file to save')

    # Parse Arguments
    parser._parse_known_args(sys.argv[1:], argparse.Namespace())
    args = parser.parse_args()


    # Create a S3 boto connect , make sure these env vars are set:  AWS_SECRET_ACCESS_KEY, AWS_ACCESS_KEY_ID
    s3 = boto3.client('s3')    
    try:
        # List Bucket
        response = s3.list_buckets() 
        
        # Convert the response to a dictionary of buckets names as key to None value. value will set to 'ServerSideEncryptionConfiguration' if one has found
        buckets = ({ bucket["Name"]:None for bucket in response['Buckets'] }) 
        
        # Create Async tasks list
        async_tasks = []

        # Iterate the bucket keys
        for bucket in list(buckets):
            print("Create task for %s" % bucket)
            async_tasks.append( 
                loop.create_task( retrieveSecurityPolicy(s3, buckets, bucket )) 
                )

        print("Please wait while background task is completed")
        await asyncio.wait(async_tasks)
        
        
        # Finally dump result to file
        with open(f'{args.save}', 'w') as file:
            yaml.dump(buckets, file)

    except Exception as e:
        logging.error(e)
        return False

    return True

# Progam Start
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except Exception as e:
        logging.error(e)
    finally:
        loop.close()
    