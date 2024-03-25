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
logger.setLevel("INFO")

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

def parse_context(context, tree, job_url, logger):
    if "boards.greenhouse.io" in job_url:
        if len(context) == 1:
            schema = json.loads(context[0].strip("\n").strip())
        else:
            #this is greenhouse specific
            flash_pending = tree.xpath(f'/html//div[@class="flash-pending"]/text()')
            if flash_pending:
                #this will happen if the job has been closed or the url was invalid
                message = flash_pending[0]
                logger.info(f"{job_url}: {message}")

    # if "comeet.com" in job_url:
    #     #TODO comeet will redirect to the company page if the job is stale. we need to account for this.
    #     # the way we can tell is that for a job description, there will be a POSITION_DATA JS field that will be non-null
    #     # for a company page meanwhile, there will be a non-null COMPANY_POSITIONS_DATA field
    #     #check if this is a job listing or a company page
    #     script = tree.xpath('/html//script[@type="text/javascript"]/text()')
    #     is_job_posting = any(["COMPANY_POSITIONS_DATA = null;" in s for s in script])
    #     is_company_page = any(["POSITION_DATA = null;" in s for s in script])
    #
    #     if is_job_posting:
    #
    #         context2 = context[0].replace("\n", "").replace("    ", "")[:-1]
    #         schema = json.loads(context2)
    #
    #     elif is_company_page:


    return schema





def get_job_data(job_url: str) -> Optional[Dict[str,Any]]:
    """get job description metadata from a JD url
    right now this only supports greenhouse (boards.greenhouse.io) JDs
    """
    schema = None
    resp = requests.get(job_url)
    tree = html.fromstring(resp.content.decode("utf-8"))
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

def search_jobs(search_term: str="data scientist", site:str="boards.greenhouse.io", max_results:int=100) -> List[str]:

    company_sites = list()
    with DDGS() as ddgs:
        links = [r["href"] for r in ddgs.text(f"{search_term} site:{site}", max_results=max_results)]
    for link in tqdm(links):
        if site =="boards.greenhouse.io" and "jobs" not in link.split("/"):
            company_sites.append(link)
            links.remove(link)

        if site =="comeet.com/jobs":
            #FIXME this is sort of wasteful if it is a real job because we are making the request twice
            resp = requests.get(link)
            if resp.url != link: #redirected
                company_sites.append(link)
                links.remove(link)


    for company in tqdm(company_sites):
        if site =="comeet.com/jobs":
            raise NotImplementedError("need to write logic for fetching urls from comeet company sites")
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

def lambda_handler(event, context):

    search_term = event.get("search_term","data scientist")
    links = search_jobs(search_term=search_term)
    data = [get_job_data(job_url) for job_url in tqdm(links)]
    data_json = {url: d for url, d in zip(links, data) if data}
    s3_url = write_data_to_s3(data=data_json,search_term=search_term)
    logger.info(f"{len(data_json)} jobs data written to {s3_url}")

    #invoke next lambda and pass data_json as the event to the next lambda

    client = boto3.client("lambda")
    arn = "arn:aws:lambda:us-east-1:652060930823:function:split-jobs"
    client.invoke(
        FunctionName=arn,
        #invoke asynchronously so we don't wait for completion
        InvocationType='Event',
        Payload=json.dumps({"jobs_data": s3_url})
    )

    logger.info("split jobs lambda invoked succesfully")


    return {'statusCode': 200, 's3url': s3_url, 'num_jobs': len(data_json)}