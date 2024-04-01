from typing import Dict, Optional, Any
from lxml import html
import boto3
from user_agent import generate_user_agent
from aiohttp import  ClientResponseError, ClientSession, ClientTimeout, TCPConnector
from tqdm import tqdm
import asyncio
import tenacity as tn
from asyncio.exceptions import TimeoutError
import json
from logging import getLogger
from time import time_ns

logger = getLogger(__name__)
logger.setLevel("INFO")


@tn.retry(retry=tn.retry_if_exception_type(TimeoutError), stop=tn.stop_after_attempt(10),
          wait=tn.wait_exponential(multiplier=1, min=4, max=10))
async def fetch(client, url):
    """FIXME factor out to utils.py"""
    try:
        headers = {'User-Agent': generate_user_agent(),
                #   'accept': '*/*',
                   #'accept-encoding': 'gzip, deflate, br',
                 #  'accept-language': 'en-US,en;q=0.9',
                   'referer': 'https://www.google.com'

                   }
        async with client.get(url, headers=headers) as resp:
            if resp.status == 200:
                content = await resp.content.read()
                return {"status": 200, "content": content}
            else:
                return {"status": resp.status, "content": None}

    except ClientResponseError as e:
        return {"status": e.status, "content": e.message}
    except Exception as e:
        if isinstance(e, TimeoutError):
            raise TimeoutError
        else:
            return {"status": None, "content": e}
#
# def get_jobs_from_company(company_url: str,
#                           base_url="https://boards.greenhouse.io") -> List[str]:
#
#     """From a listing of jobs at a company, return the list of urls for job postings that are relevant to the search term"""
#
#     html_resp = requests.get(company_url)
#    # html_resp = company.content.decode("utf-8")
#     tree = html.fromstring(html_resp)
#     #data-mapped attribute may be greenhouse specific. we select this so that we don't get the
#     #"Privacy Policy" link which doesn't have a second .values()
#     anchors = tree.xpath('/html/body//a[@data-mapped]')
#     job_urls = list()
#     for a in anchors:
#         if not a.text:
#             #account for cases like <span>Powered by</span>&nbsp;<a target="_blank" href="http://www.greenhouse.io/">
#             continue
#
#         job_url = a.values()[1]
#         #greenhouse specific
#         if "/jobs/" in job_url:
#             if not job_url.startswith(base_url):
#                 job_url = urljoin(base_url, job_url)
#             job_urls.append(job_url)
#     return job_urls
#
# def process_company_site(html_resp: str,
#                                base_url="https://boards.greenhouse.io", ) -> List[str]:
#
#     """From a listing of jobs at a company, return the list of urls for job postings that are relevant to the search term"""
#
#     tree = html.fromstring(html_resp)
#     #data-mapped attribute may be greenhouse specific. we select this so that we don't get the
#     #"Privacy Policy" link which doesn't have a second .values()
#     anchors = tree.xpath('/html/body//a[@data-mapped]')
#     job_urls = list()
#     for a in anchors:
#         if not a.text:
#             #account for cases like <span>Powered by</span>&nbsp;<a target="_blank" href="http://www.greenhouse.io/">
#             continue
#
#         job_url = a.values()[1]
#         #greenhouse specific
#         if "/jobs/" in job_url:
#             if not job_url.startswith(base_url):
#                 job_url = urljoin(base_url, job_url)
#             job_urls.append(job_url)
#
#     return job_urls
#
# def ls_s3(bucket="scrapedjobs", **kwargs):
#     """
#
#     Args:
#         bucket:
#         Prefix: the prefix to filter the s3 bucket on
#
#     Returns:
#
#     """
#     s3 = boto3.resource('s3')
#     bucket = s3.Bucket(bucket)
#     keys = [o.key for o in tqdm(bucket.objects.filter(**kwargs))]
#     return keys
#
#
# def get_company_urls(s3_prefix: str = "deduped") -> List[str]:
#
#     def company_url_from_s3_prefix(prefix: str) -> str:
#         company_url = "/".join(
#             prefix.split("/", 3)[1:3])
#         company_url = f"https://{company_url}"
#         return company_url
#
#     #TODO pass "deduped/boards.greenhouse.io" filter condition directly to list_objects?
#     s3urls = ls_s3(Prefix=s3_prefix)
#     greenhouse_urls = [s3url for s3url in s3urls if "deduped/boards.greenhouse.io" in s3url]
#     company_urls = [company_url_from_s3_prefix(s3_prefix) for s3_prefix in greenhouse_urls]
#     return company_urls


async def async_fetch_jobs(urls):
    async_session = ClientSession(
        raise_for_status=False, timeout=ClientTimeout(total=120), connector=TCPConnector(ssl=False)
    )
    asynch_requests = [fetch(async_session, url) for url in tqdm(urls)]

    r = await asyncio.gather(*asynch_requests)
    await async_session.close()
    return r



def get_job_data(jd:str, job_url) -> Optional[Dict[str,Any]]:
    """get job description metadata from a JD url
    right now this only supports greenhouse (boards.greenhouse.io) JDs
    """
    schema = None
    tree = html.fromstring(jd)
    if tree.text == "The board you are looking for is no longer open.":
        logger.info(f"Job board closed for url {job_url}")
    else:
        # the json schema for the greenhouse JDs comes after this javascript tag
        context = tree.xpath(f'/html/body/script[@type="application/ld+json"]/text()')
        if len(context) == 1:
            schema = json.loads(context[0].strip("\n").strip())
        else:
            #this is greenhouse specific
            flash_pending = tree.xpath(f'/html//div[@class="flash-pending"]/text()')
            if flash_pending:
                #this will happen if the job has been closed or the url was invalid
                message = flash_pending[0]
                logger.info(f"{job_url}: {message}")


    return schema



def write_data_to_s3(data: dict, bucket_name: str = "scrapedjobs", client=None):
    client = client or boto3.client("s3")

    timestamp = int(time_ns())
    key = f"{timestamp}/all_titles.json"

    client.put_object(
        Body=json.dumps(data),
        Bucket=bucket_name,
        Key=key
    )
    return f"s3://{bucket_name}/{key}"


def lambda_handler(event,context):
    """
    Visit job urls to scrape individual job descriptions
    Args:
        event:
        context:

    Returns:

    """
    job_urls = list()
    companies_jobs = event["jobs"]
    base_url = event.get("base_url", "https://boards.greenhouse.io")

    #reconstruct urls from {"company_name": [job_id, job_id]} dict
    for company, job_ids in companies_jobs.items():
        for job_id in job_ids:
            job_url = f"{base_url}/{company}/jobs/{job_id}"
            job_urls.append(job_url)

    #scrape
    responses = asyncio.run(async_fetch_jobs(job_urls))

    url_jd = dict()
    for resp, url in tqdm(zip(responses, job_urls),"job response"):
        content = resp["content"]
        if content:
            decoded = content.decode("utf-8")
            job_description = get_job_data(decoded, url)
            url_jd[url] = job_description


    s3_url = write_data_to_s3(data=url_jd)
    logger.info(f"{len(url_jd)} jobs data written to {s3_url}")
    #TODO need to trigger split jobs
    return {'statusCode': 200, "s3_url": s3_url, 'num_jobs': len(url_jd)}



#I want to split jobs, but at the same time trigger sns alert for new jobs.
#so when I check to see if a job is new in split_jobs, I can also trigger an SNS alert for that.
#I think for now we should just use boto3 to do the sns alerts,
#however later we can probably do this directly in step functions.
#ah, so here is probably why you want to split off the alerting - you want filter conditions.
#do we alert for data scientist jobs, or ml engineer jobs, or what?
#the thing is that you want to be able to easily change your filter conditions without going in and updating a lambda.
#so there's definitely a way to do this with "choice" states in step functions.
#I think for the v0 I should just embed the logic within the lambda
#then v1 can be a json or something on s3
#then v2 can be using step functions choice state.

