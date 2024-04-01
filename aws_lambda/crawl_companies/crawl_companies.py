from typing import List, Dict
from lxml import html
from urllib.parse import urljoin
import boto3
from user_agent import generate_user_agent
from aiohttp import  ClientResponseError, ClientSession, ClientTimeout, TCPConnector
from tqdm import tqdm
import asyncio
import tenacity as tn
from asyncio.exceptions import TimeoutError
import json
from logging import getLogger


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

def process_company_site(html_resp: str,
                               base_url="https://boards.greenhouse.io", ) -> List[str]:

    """From a listing of jobs at a company, return the list of urls for job postings that are relevant to the search term"""

    tree = html.fromstring(html_resp)
    #data-mapped attribute may be greenhouse specific. we select this so that we don't get the
    #"Privacy Policy" link which doesn't have a second .values()
    anchors = tree.xpath('/html/body//a[@data-mapped]')
    job_urls = list()
    for a in anchors:
        if not a.text:
            #account for cases like <span>Powered by</span>&nbsp;<a target="_blank" href="http://www.greenhouse.io/">
            continue

        job_url = a.values()[1]
        #greenhouse specific
        if "/jobs/" in job_url:
            if not job_url.startswith(base_url):
                job_url = urljoin(base_url, job_url)
            job_urls.append(job_url)

    return job_urls

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


def get_company_urls(s3_prefix: str = "deduped") -> List[str]:

    def company_url_from_s3_prefix(prefix: str) -> str:
        company_url = "/".join(
            prefix.split("/", 3)[1:3])
        company_url = f"https://{company_url}"
        return company_url

    #TODO pass "deduped/boards.greenhouse.io" filter condition directly to list_objects?
    s3urls = ls_s3(Prefix=s3_prefix)
    greenhouse_urls = [s3url for s3url in s3urls if "deduped/boards.greenhouse.io" in s3url]
    company_urls = [company_url_from_s3_prefix(s3_prefix) for s3_prefix in greenhouse_urls]
    return company_urls


async def async_fetch_jobs(urls):
    async_session = ClientSession(
        raise_for_status=False, timeout=ClientTimeout(total=120), connector=TCPConnector(ssl=False)
    )
    asynch_requests = [fetch(async_session, url) for url in tqdm(urls)]

    r = await asyncio.gather(*asynch_requests)
    await async_session.close()
    return r


from collections import defaultdict


def make_companies_dict(urls: List[str]) ->Dict[str,str]:
    """

    Args:
        urls:

    Returns: Dict of {company_name: [job_id, job_id...],..}

    """
    companies = defaultdict(list)
    for url in urls:
        companies[url.split("/")[3]].append(url.split("/")[5])
    return companies



def lambda_handler(event,context):
    """
    Visit company sites in scrapedjobs/deduped and check them for jobs. This returns all jobs, not just new ones
    Args:
        event:
        context:

    Returns:

    """
    all_job_urls = list()

    prefix = event.get("s3_prefix","deduped")
    company_urls = get_company_urls(s3_prefix=prefix)

    responses = asyncio.run(async_fetch_jobs(company_urls))

    for resp in tqdm(responses,"company response"):
        content = resp["content"]
        if content:
            decoded = content.decode("utf-8")
            company_job_urls = process_company_site(decoded)
            all_job_urls.extend(company_job_urls)

    companies_jobs = make_companies_dict(all_job_urls)
    return {'statusCode': 200, "jobs": json.dumps(companies_jobs), 'num_jobs': len(all_job_urls)}



