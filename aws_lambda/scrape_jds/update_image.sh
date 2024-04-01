docker build --platform linux/amd64 -t scrape-jds:latest .
docker tag scrape-jds:latest 652060930823.dkr.ecr.us-east-1.amazonaws.com/scrape-jds:latest
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin  652060930823.dkr.ecr.us-east-1.amazonaws.com
docker push 652060930823.dkr.ecr.us-east-1.amazonaws.com/scrape-jds:latest
aws lambda update-function-code \
    --function-name scrape-jds \
    --image-uri 652060930823.dkr.ecr.us-east-1.amazonaws.com/scrape-jds:latest