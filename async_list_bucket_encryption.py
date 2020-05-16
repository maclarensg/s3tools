#!/usr/bin/env python
import asyncio
import aiobotocore
import sys, argparse
import yaml
import asyncio
from botocore.exceptions import ClientError


async def retrieveSecurityPolicy(s3, buckets, bucket):
    try:
        # Get each buck name encryption
        response = await s3.get_bucket_encryption(
            Bucket=bucket
        )

        # Print indicator when a bucket has response
        print("%s\n" %  bucket, end="", flush=True)

        # When a encyption info is found save to dictionary 
        if "ServerSideEncryptionConfiguration" in response and "Rules" in response["ServerSideEncryptionConfiguration"] and len(response["ServerSideEncryptionConfiguration"]["Rules"]) > 0:
            for rule in response["ServerSideEncryptionConfiguration"]["Rules"]:
               if "ApplyServerSideEncryptionByDefault" in rule and "SSEAlgorithm" in rule["ApplyServerSideEncryptionByDefault"]:
                    if rule["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"] == "aws:kms":
                        del buckets[bucket]
                    else: 
                        buckets[bucket] = response["ServerSideEncryptionConfiguration"]

    except ClientError:
        # Print indicator when a bucket has response
        print("%s\n" % bucket , end="", flush=True)
        pass
    
# Main Program
async def main():
    # Argument parser
    parser = argparse.ArgumentParser(description='List and audit s3 buckets, return buckets without encryption or encryption other than kms', 
                                     argument_default=argparse.SUPPRESS)

    parser.add_argument('--save', metavar='file',
                        default='audit.yml', 
                        help='file to save')

    # Parse Arguments
    parser._parse_known_args(sys.argv[1:], argparse.Namespace())
    args = parser.parse_args()

    try:
        session = aiobotocore.get_session()
        async with session.create_client('s3') as s3:

            resp  = await s3.list_buckets() 

            buckets = ({ bucket["Name"]:None for bucket in resp['Buckets'] }) 
        
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
    
    return True # Return Main

    
# Progam Start
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except Exception as e:
        logging.error(e)
    finally:
        loop.close()
    