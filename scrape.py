import requests
from lxml import html
from typing import Dict, Any, List, Optional
import json
from urllib.parse import urljoin
from duckduckgo_search import DDGS
from tqdm import tqdm
def get_jobs_from_company(company_url: str, search_term: str = "data scientist",
                          base_url="https://boards.greenhouse.io") -> List[str]:
    """From a listing of jobs at a company, return the list of urls for job postings that are relevant to the search term"""

    company = requests.get(company_url)
    html_resp = company.content.decode("utf-8")
    tree = html.fromstring(html_resp)
    anchors = tree.xpath(f'/html/body//a')
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
        #this is greenhouse specific
        job_closed = 'The job you are looking for is no longer open.' in tree.xpath(
            f'/html//div[@class="flash-pending"]/text()')
        if job_closed:
            schema = None
        else:
            raise RuntimeError("Length of context not equal to 1. Did not detect closed job")

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