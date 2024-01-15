# Kyte Lambda Scripts

[![Deploy to CDN](https://github.com/keyqcloud/kyte-lambda-update-shipyard/actions/workflows/main.yml/badge.svg)](https://github.com/keyqcloud/kyte-lambda-update-shipyard/actions/workflows/main.yml) [![CodeQL](https://github.com/keyqcloud/kyte-api-python/actions/workflows/codeql.yml/badge.svg)](https://github.com/keyqcloud/kyte-api-python/actions/workflows/codeql.yml)

This repository contains AWS Lambda scripts for managing Kyte-related operations. The Lambda scripts can be set up manually or deployed using the provided CloudFormation template.

## CloudFormation

For automated setup, use the Kyte CloudFormation script available at [Kyte CloudFormation Repository](https://github.com/keyqcloud/kyte-cloudformation). This script handles necessary configurations including SNS topics and permissions.

## Manual Setup

For manual configuration, ensure that the required SNS topics and permissions are properly set up as per the requirements of each Lambda script.

## kyte-update-shipyard

This Lambda script manages the creation and deletion of Kyte sites. It has a timeout of 10 minutes to accommodate configuration times required for certain resources, such as S3.

### Environmental Variables

- `kyte_shipyard_s3`: S3 bucket name for Kyte Shipyard
- `kyte_shipyard_cf`: CloudFront distribution ID for Kyte Shipyard.

### Required IAM Execution Role
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "arn:aws:logs:[region]:[account]:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:[region]:[account]:log-group:/aws/lambda/kyte-update-shipyard:*"
            ]
        },
		{
			"Effect": "Allow",
			"Action": [
				"s3:*",
				"s3-object-lambda:*"
			],
			"Resource": "arn:aws:s3:::[s3_bucket_for_kyte_shipyard]/*"
		},
		{
			"Effect": "Allow",
			"Action": [
				"cloudfront:GetDistribution",
				"cloudfront:CreateInvalidation"
			],
			"Resource": [
				"arn:aws:cloudfront::[account]:distribution/[distribution_id_for_kyte_shipyard]"
			]
		}
    ]
}
```