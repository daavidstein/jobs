import requests
from lxml import html
from typing import Dict, Any
import json
from urllib.parse import urljoin
def get_jobs_from_company(company_url: str, search_term: str = "data scientist",
                          base_url="https://boards.greenhouse.io"):
    """From a listing of jobs at a company, return the list of urls for job postings that are relevant to the search term"""

    company = requests.get(company_url)
    html_resp = company.content.decode("utf-8")
    tree = html.fromstring(html_resp)
    anchors = tree.xpath(f'/html/body//a')
    new_links = list()
    for a in anchors:
        if search_term.lower() in a.text.lower():
            new_link = a.values()[1]
            if not new_link.startswith(base_url):
                new_link = urljoin(base_url, new_link)
            new_links.append(new_link)
    return new_links


def get_job_data(job_url: str) -> Dict[str,Any]:
    """get job description metadata from a JD url
    right now this only supports greenhouse (boards.greenhouse.io) JDs
    """
    resp = requests.get(job_url)
    tree = html.fromstring(resp.content.decode("utf-8"))
    #the json schema for the greenhouse JDs comes after this javascript tag
    context = tree.xpath(f'/html/body/script[@type="application/ld+json"]/text()')
    assert len(context) == 1
    schema = json.loads(context[0].strip("\n").strip())
    return schema