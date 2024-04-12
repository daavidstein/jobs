#!/usr/bin/env bash
aws lambda create-function \
    --function-name $1 \
    --image-uri $(echo ${AWS_ACCT_ID}).dkr.ecr.$(echo ${AWS_REGION}).amazonaws.com/$1:latest

aws logs create-log-group --log-group-name /aws/lambda/$1