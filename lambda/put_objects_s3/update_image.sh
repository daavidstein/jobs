docker build --platform linux/amd64 -t put-objects-s3:latest .
docker tag put-objects-s3:latest 652060930823.dkr.ecr.us-east-1.amazonaws.com/put-objects-s3:latest
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin  652060930823.dkr.ecr.us-east-1.amazonaws.com
docker push 652060930823.dkr.ecr.us-east-1.amazonaws.com/put-objects-s3:latest
aws lambda update-function-code \
    --function-name put-objects-s3 \
    --image-uri 652060930823.dkr.ecr.us-east-1.amazonaws.com/put-objects-s3:latest



aws lambda create-function \
    --function-name put-objects-s3 \

    --image-uri 652060930823.dkr.ecr.us-east-1.amazonaws.com/put-objects-s3:latest