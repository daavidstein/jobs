docker build --platform linux/amd64 -t $1:latest .
docker tag $1:latest 652060930823.dkr.ecr.us-east-1.amazonaws.com/$1:latest
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin  652060930823.dkr.ecr.us-east-1.amazonaws.com
docker push 652060930823.dkr.ecr.us-east-1.amazonaws.com/$1:latest
aws lambda update-function-code \
    --function-name $1 \
    --image-uri 652060930823.dkr.ecr.us-east-1.amazonaws.com/$1:latest