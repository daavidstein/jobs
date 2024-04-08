from typing import List, Dict
from lxml import html
from urllib.parse import urljoin
import json
from logging import getLogger
import requests
from collections import defaultdict

logger = getLogger(__name__)
logger.setLevel("INFO")

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


def company_url_from_s3_prefix(prefix: str) -> str:
    company_url = "/".join(
        prefix.split("/", 3)[1:3])
    company_url = f"https://{company_url}"
    return company_url




def make_companies_dict(urls: List[str]) ->Dict[str,List[str]]:
    """

    Args:
        urls:

    Returns: Dict of {company_name: [job_id, job_id...],..}

    """
    companies = defaultdict(list)
    for url in urls:
        companies[url.split("/")[3]].append(url.split("/")[5])
    return dict(companies)



def lambda_handler(event,context):
    """
    Visit company sites in scrapedjobs/deduped and check them for jobs. This returns all jobs, not just new ones
    Args:
        event:
        context:

    Returns:

    """
    all_job_urls = list()

    company_prefix = event.get("company_prefix")
    company_url = company_url_from_s3_prefix(company_prefix)
    response = requests.get(company_url)
    content = response.content
    if content:

        decoded = content.decode("utf-8")

        company_job_urls = process_company_site(decoded)
        all_job_urls.extend(company_job_urls)

    companies_jobs = make_companies_dict(all_job_urls)
    companies_jobs_array = [{k:v} for k,v in companies_jobs.items() if v]

    return {'statusCode': 200, "jobs": json.dumps(companies_jobs_array), 'num_jobs': len(all_job_urls),"num_companies": len(companies_jobs)}



