import boto3
import requests
import time
import zipfile
import io
import os
import re
import json
import logging
import mimetypes

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# URL of the CHANGELOG.md
changelog_url = 'http://cdn.keyqcloud.com/kyte/shipyard/archive/CHANGELOG.md'
# URL of the zip file
zip_file_url = 'http://cdn.keyqcloud.com/kyte/shipyard/stable/kyte-shipyard.zip'
# S3 bucket name
s3_bucket = os.environ['kyte_shipyard_s3']

s3_client = boto3.client('s3')

def get_latest_version_from_changelog(url):
    response = requests.get(url)
    if response.status_code == 200:
        content = response.text
        # Regex to find version numbers in the format ## X.Y.Z
        versions = re.findall(r'## (\d+\.\d+\.\d+)', content)
        if versions:
            return versions[0]  # Returns the first version found, which should be the latest
    return None

def download_and_extract_zip(url):
    response = requests.get(url)
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as thezip:
            # Extract all the contents into /tmp/ directory
            thezip.extractall('/tmp/')
            logger.info("Zip file downloaded and extracted successfully.")
            return thezip.namelist()
    else:
        raise Exception(f"Failed to download or extract zip file. Status code: {response.status_code}")

def upload_files_to_s3(file_names, bucket_name):
    for file_name in file_names:
        file_path = os.path.join('/tmp/', file_name)
        try:
            # Upload file to S3 bucket
            content_type = mimetypes.guess_type(file_path)[0]
            s3_client.upload_file(file_path, bucket_name, file_name, ExtraArgs={'ContentType': content_type})
            logger.info(f"Uploaded {file_name} to S3 bucket {bucket_name}")

        except Exception as e:
            logger.error(f"Failed to upload {file_name} to S3. Error: {str(e)}")

def lambda_handler(event, context):
    try:
        for record in event['Records']:
            body = json.loads(record['Sns']['Message'])
            current_version = body['current_version'] if 'current_version' in body else None
            if current_version is None:
                raise Exception("Failed to determine current version of Kyte Shipyard")

            latest_version = get_latest_version_from_changelog(changelog_url)
            if latest_version is None:
                raise Exception("Failed to determine the latest version from CHANGELOG.md")

            if latest_version != current_version:
                logger.info(f"New version available: {latest_version}. Current version: {current_version}. Updating...")

                # Download and extract the zip file
                extracted_files = download_and_extract_zip(zip_file_url)

                # Upload extracted files to S3
                upload_files_to_s3(extracted_files, s3_bucket)

                # Invalidate CloudFront distribution
                cloudfront_client = boto3.client('cloudfront')
                cloudfront_distribution_id = os.environ['kyte_shipyard_cf']
                cloudfront_client.create_invalidation(
                    DistributionId=cloudfront_distribution_id,
                    InvalidationBatch={
                        'Paths': {
                            'Quantity': 1,
                            'Items': [ '/*' ]
                        },
                        'CallerReference': str(time.time()).replace('.', '')
                    }
                )

            else:
                logger.info(f"Current version ({current_version}) is up to date.")

        return {
            'statusCode': 200,
            'body': f'Update check complete. Current version: {current_version}, Latest version: {latest_version}'
        }
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error in lambda_handler: {str(e)}"
        }