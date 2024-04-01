
from tqdm import tqdm
import boto3
from logging import getLogger
import json
logger = getLogger(__name__)
logger.setLevel("INFO")



def lambda_handler(event, context):
    keys = event["s3_keys"]
    client = boto3.client("s3")
    for key in tqdm(keys):
        client.put_object(
            Body=json.dumps("this is a dummy object for creating an s3 prefix"),
            Bucket="scrapedjobs",
            Key=key
        )


    return {'statusCode': 200, 's3_keys': keys, 'num_companies': len(keys)}