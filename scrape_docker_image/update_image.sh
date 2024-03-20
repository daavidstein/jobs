docker build --platform linux/amd64 -t scrape-jobs:latest .
docker tag scrape-jobs:latest 652060930823.dkr.ecr.us-east-1.amazonaws.com/scrape:latest
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin  652060930823.dkr.ecr.us-east-1.amazonaws.com
docker push 652060930823.dkr.ecr.us-east-1.amazonaws.com/scrape:latest