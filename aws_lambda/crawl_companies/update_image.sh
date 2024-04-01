#docker build --platform linux/amd64 -t crawl-companies:latest .
#docker tag crawl-companies:latest 652060930823.dkr.ecr.us-east-1.amazonaws.com/crawl-companies:latest
#aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin  652060930823.dkr.ecr.us-east-1.amazonaws.com
#docker push 652060930823.dkr.ecr.us-east-1.amazonaws.com/crawl-companies:latest
#aws lambda update-function-code \
#    --function-name crawl-companies \
#    --image-uri 652060930823.dkr.ecr.us-east-1.amazonaws.com/crawl-companies:latest
../update_lambda.sh crawl-companies