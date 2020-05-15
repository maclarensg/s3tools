#!/usr/bin/env python
import logging
import boto3
import sys, argparse
import yaml
from botocore.exceptions import ClientError


# Main Program
def main():

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
        
        # Iterate the bucket keys
        for bucket in list(buckets):
            print(".", end='', flush=True)
            try:
                # Get each buck name encryption
                response = s3.get_bucket_encryption(
                    Bucket=bucket
                )

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

        print("Done")
        
        # Finally dump result to file
        with open(f'{args.save}', 'w') as file:
            yaml.dump(buckets, file)

    except Exception as e:
        logging.error(e)
        return False

    return True

# Progam Start
if __name__ == "__main__":
    main()