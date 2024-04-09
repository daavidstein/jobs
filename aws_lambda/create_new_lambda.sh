#!/usr/bin/env bash
aws lambda create-function \
    --function-name $1 \
    --image-uri 652060930823.dkr.ecr.us-east-1.amazonaws.com/$1:latest

aws logs create-log-group --log-group-name /aws/lambda/$1