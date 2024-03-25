import json
from typing import Dict, Any, List, Tuple
import boto3
from tqdm import tqdm
from logging import getLogger
logger = getLogger(__name__)
logger.setLevel("INFO")

def ls_s3(bucket="scrapedjobs", **kwargs):
    """

    Args:
        bucket:
        Prefix: the prefix to filter the s3 bucket on

    Returns:

    """
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket)
    keys = [o.key for o in tqdm(bucket.objects.filter(**kwargs))]
    return keys



def dedupe_keys(existing_keys: List[str], jobs: Dict[str,Any], prefix: str)->Dict[str,Any]:
    """compare the freshly scraped jobs to existing s3 keys in scrapedjobs/deduped and return only the new ones"""


    #compare the fresh http urls, after removing ? and
    new_jobs = {clean_url(job_url): data for job_url, data in jobs.items() if
                job_url_to_s3key(job_url) not in existing_keys}
    return new_jobs


def job_url_to_s3key(job_url: str, new_prefix=None) -> str:
    job_url = clean_url(job_url)
    key = job_url.removeprefix("https://").removeprefix("http://")
    if new_prefix:
        key = f"{new_prefix}/{key}"
    return key


def clean_url(url: str) -> str:
    """Remove query bit from some greenhouse urls like boards.greenhouse.io/6sense/jobs/5567149?gh_jid=5567149"""

    url = url.split("?")[0]
    return url

def get_json_s3(key: str, bucket="scrapedjobs", client=None):

    client = client or boto3.client("s3")
    obj =client.get_object(
    Bucket=bucket,
    Key=key
)
    return json.loads(obj["Body"].read())


def split_s3url(s3url: str) -> Tuple[str,str]:
    """from an s3url, extract the bucket and key"""
    noprotocol = s3url.removeprefix("s3://")
    bucket = noprotocol.split("/")[0]
    key = "/".join(noprotocol.split("/")[1:])
    return bucket, key

def lambda_handler(event: str, context):
    """
    Split a json of url: data into individual jsons with one top-level key/pair each, providing the key hasn't
    been seen before.

    Args:
     event:

    Returns:
    """

    client = boto3.client("s3")

    #jobs_data_s3url = event["jobs_data"]
    jobs_data_s3url = event["s3url"]

    bucket_name, key = split_s3url(jobs_data_s3url)
    prefix = event.get("prefix", "deduped/")
   # bucket_name = event.get("bucket_name","scrapedjobs")

    jobs_data = get_json_s3(key=key, bucket=bucket_name, client = client)

    #existing_jobs start with prefix
    existing_keys = ls_s3(bucket=bucket_name, Prefix=prefix)
    new_jobs = dedupe_keys(existing_keys, jobs_data, prefix)


    for job_url, data in tqdm(new_jobs.items()):
        if data:
            key = f"deduped/{job_url_to_s3key(job_url)}.json"
            client.put_object(
                Body=json.dumps(data),
                Bucket=bucket_name,
                Key=key
            )
    s3url =  f"s3://{bucket_name}/{key}"
    logger.info(f"{ len(new_jobs) } new jobs written to {s3url}")
    return {'statusCode': 200, 's3url':s3url, 'num_jobs': len(new_jobs)}
