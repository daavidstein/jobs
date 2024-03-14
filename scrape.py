import requests
from lxml import html
from typing import Dict, Any, List, Optional
import json
from urllib.parse import urljoin
from duckduckgo_search import DDGS
from tqdm import tqdm
from logging import getLogger
import boto3
from time import time_ns
logger = getLogger(__name__)

def get_jobs_from_company(company_url: str, search_term: str = "data scientist",
                          base_url="https://boards.greenhouse.io") -> List[str]:

    """From a listing of jobs at a company, return the list of urls for job postings that are relevant to the search term"""

    company = requests.get(company_url)
    html_resp = company.content.decode("utf-8")
    tree = html.fromstring(html_resp)
    anchors = tree.xpath('/html/body//a')
    new_links = list()
    for a in anchors:
        if not a.text:
            #account for cases like <span>Powered by</span>&nbsp;<a target="_blank" href="http://www.greenhouse.io/">
            continue
        if search_term.lower() in a.text.lower():
            new_link = a.values()[1]
            if not new_link.startswith(base_url):
                new_link = urljoin(base_url, new_link)
            new_links.append(new_link)
    return new_links


def get_job_data(job_url: str) -> Optional[Dict[str,Any]]:
    """get job description metadata from a JD url
    right now this only supports greenhouse (boards.greenhouse.io) JDs
    """
    resp = requests.get(job_url)
    tree = html.fromstring(resp.content.decode("utf-8"))
    #the json schema for the greenhouse JDs comes after this javascript tag
    context = tree.xpath(f'/html/body/script[@type="application/ld+json"]/text()')
    if len(context) == 1:
        schema = json.loads(context[0].strip("\n").strip())
    else:
        schema = None
        #this is greenhouse specific
        job_closed = 'The job you are looking for is no longer open.' in tree.xpath(
            f'/html//div[@class="flash-pending"]/text()')
        if job_closed:
            logger.info(f"Job closed for url {job_url}")
        else:
            logger.info(f"Length of context not equal to 1. Did not detect closed job. url: {job_url}")

    return schema

def search_jobs(search_term: str="data scientist", site:str="boards.greenhouse.io", max_results:int=100) -> List[str]:

    company_sites = list()
    with DDGS() as ddgs:
        links = [r["href"] for r in ddgs.text(f"{search_term} site:{site}", max_results=max_results)]
    for link in tqdm(links):
        if "jobs" not in link.split("/"):
            company_sites.append(link)
            links.remove(link)

    for company in tqdm(company_sites):
        #TODO async
        company_jobs = get_jobs_from_company(company)
        links.extend(company_jobs)

    return links


def write_data_to_s3(data: dict, search_term: str, bucket_name: str = "scrapedjobs", client=None):
    client = client or boto3.client("s3")

    timestamp = int(time_ns())
    key = f"{timestamp}/{search_term.replace(' ', '_')}.json"

    client.put_object(
        Body=json.dumps(data),
        Bucket=bucket_name,
        Key=key
    )
    return f"s3://{bucket_name}/{key}"

def job_url_to_s3key(job_url: str, new_prefix=None) -> str:
    job_url = clean_url(job_url)
    key = job_url.removeprefix("https://").removeprefix("http://")
    if new_prefix:
        key = f"{new_prefix}/{key}"
    return key

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

def clean_url(url: str) -> str:
    """Remove query bit from some greenhouse urls like boards.greenhouse.io/6sense/jobs/5567149?gh_jid=5567149"""

    url = url.split("?")[0]
    return url



def write_new_jobs(jobs: Dict[str,Any], bucket_name = "scrapedjobs"):
    """
    Split a json of url: data into individual jsons with one top-level key/pair each, providing the key hasn't
    been seen before.

    Args:
     jobs:
     bucket_name:

    Returns:
    """
    prefix="deduped/"
    #existing_jobs start with prefix
    existing_keys = ls_s3(bucket=bucket_name, Prefix=prefix)
    new_jobs = dedupe_keys(existing_keys, jobs, prefix)

    client = boto3.client("s3")

    for job_url, data in tqdm(new_jobs.items()):
        if data:
            key = job_url_to_s3key(job_url)
            client.put_object(
                Body=json.dumps(data),
                Bucket=bucket_name,
                Key=f"deduped/{key}.json"
            )


def dedupe_keys(existing_keys: List[str], jobs: Dict[str,Any], prefix: str)->Dict[str,Any]:
    """compare the freshly scraped jobs to existing s3 keys in scrapedjobs/deduped and return only the new ones"""


    #compare the fresh http urls, after removing ? and
    new_jobs = {clean_url(job_url): data for job_url, data in jobs.items() if
                job_url_to_s3key(job_url) not in existing_keys}
    return new_jobs


if __name__ == "__main__":
    search_term = "data scientist"
    links = search_jobs(search_term=search_term)
    data = [get_job_data(job_url) for job_url in tqdm(links)]
    data_json = {url: d for url, d in zip(links, data) if data}
    s3_url = write_data_to_s3(data=data_json,search_term=search_term)
    logger.info(f"{len(data_json)} jobs data written to {s3_url}")




#do ddg search.
# get links to scrape
#scrape directly jobs, get company links, do more scraping
#output one big json
#filter that json by urls that *aren't currently in deduped, and then pass that to another lambda, or in the same lambda do the following:
# take all the filtered (new) jobs, and output an individual json for each of them.