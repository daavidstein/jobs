#!/usr/bin/env bash
docker build --platform linux/amd64 -t $1:latest .
docker tag $1:latest ${AWS_ACCT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/$1:latest
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin  ${AWS_ACCT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
docker push ${AWS_ACCT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/$1:latest
aws lambda update-function-code \
    --function-name $1 \
    --image-uri $(echo ${AWS_ACCT_ID}).dkr.ecr.$(echo ${AWS_REGION}).amazonaws.com/$1:latest