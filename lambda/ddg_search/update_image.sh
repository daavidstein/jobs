docker build --platform linux/amd64 -t ddg-search:latest .
docker tag ddg-search:latest 652060930823.dkr.ecr.us-east-1.amazonaws.com/ddg-search:latest
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin  652060930823.dkr.ecr.us-east-1.amazonaws.com
docker push 652060930823.dkr.ecr.us-east-1.amazonaws.com/ddg-search:latest
aws lambda update-function-code \
    --function-name ddg-search \
    --image-uri 652060930823.dkr.ecr.us-east-1.amazonaws.com/ddg-search:latest