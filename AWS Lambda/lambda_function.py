import boto3
import botocore
import json
import os
import logging
import gzip
import io
import urllib.parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.resource('s3')

def lambda_handler(event, context):
    logger.info("New files uploaded to the source bucket.")
    
    # URL decode the key to handle spaces and special characters correctly
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    destination_bucket = os.environ['destination_bucket']
    
    try:
        # Download the file from the source bucket
        source_obj = s3.Object(source_bucket, key)
        file_content = source_obj.get()['Body'].read()

        # Compress the file content
        compressed_file = io.BytesIO()
        with gzip.GzipFile(fileobj=compressed_file, mode='wb') as gz:
            gz.write(file_content)
        compressed_file.seek(0)

        # Define the key for the compressed file
        compressed_key = key + '.gz'

        # Upload the compressed file to the destination bucket
        s3.Bucket(destination_bucket).put_object(Key=compressed_key, Body=compressed_file)

        logger.info("File compressed and copied to the destination bucket successfully!")
        return {
            'statusCode': 200,
            'body': json.dumps('File compressed and copied to the destination bucket successfully!')
        }
    except botocore.exceptions.ClientError as error:
        logger.error("There was an error copying the file to the destination bucket")
        print('Error Message: {}'.format(error))
        return {
            'statusCode': 500,
            'body': json.dumps('Error copying the file to the destination bucket')
        }
    except botocore.exceptions.ParamValidationError as error:
        logger.error("Missing required parameters while calling the API.")
        print('Error Message: {}'.format(error))
        return {
            'statusCode': 400,
            'body': json.dumps('Missing required parameters while calling the API')
        }
