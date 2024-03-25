from typing import List
import requests
from lxml import html
from urllib.parse import urljoin
import boto3
from tqdm import tqdm
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

    def company_url_from_s3_prefix(s3_prefix):
        company_url = "/".join(
            s3_prefix.split("/", 3)[1:3])
        company_url = company_url =f"https://{company_url}"
        return company_url

    #TODO pass "deduped/boards.greenhouse.io" filter condition directly to list_objects?
    s3urls = ls_s3(Prefix=s3_prefix)
    greenhouse_urls = [ s3url for  s3url in  s3urls if "deduped/boards.greenhouse.io" in  s3url]
    company_urls = [company_url_from_s3_prefix(s3_prefix) for s3_prefix in greenhouse_urls]
    return company_urls



""""
so should this lambda actually scrape the individual JDS and write to s3,
or should it just get the JD urls to scrape, and pass that to a new lambda?
"""