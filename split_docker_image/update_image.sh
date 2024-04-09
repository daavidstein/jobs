docker build --platform linux/amd64 -t split-jobs:latest .
docker tag split-jobs:latest ${AWS_ACCT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/split-jobs:latest
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin  ${AWS_ACCT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
docker push ${AWS_ACCT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/split-jobs:latest


aws lambda update-function-code \
    --function-name split-jobs \
    --image-uri  $(echo ${AWS_ACCT_ID}).dkr.ecr.$(echo ${AWS_REGION}).amazonaws.com/split-jobs:latest