#!/usr/bin/env bash
#first argument is directory name to create the template
#second argument is the name of the function

mkdir ./$1

echo "boto3" > ./$1/requirements.txt
echo "FROM public.ecr.aws/lambda/python:3.12

# Copy requirements.txt
COPY requirements.txt \${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY $2.py \${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ \"$2.lambda_handler\" ]" > ./$1/dockerfile


echo "from logging import getLogger

logger = getLogger(__name__)
logger.setLevel(\"INFO\")

def lambda_handler(event, context):


    return {'statusCode': 200}
" > ./$1/$2.py