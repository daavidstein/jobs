
from typing import List

from duckduckgo_search import DDGS
from logging import getLogger

logger = getLogger(__name__)
logger.setLevel("INFO")

def ddg_search(search_term: str= "data scientist", site:str= "boards.greenhouse.io", max_results:int=100) -> List[str]:

    with DDGS() as ddgs:
        links = [r["href"] for r in ddgs.text(f"{search_term} site:{site}", max_results=max_results)]

    logger.info(f"retrieved {len(links)} links from DDG search for {search_term}")
    return links

def greenhouse_job_urls_to_company_urls(greenhouse_job_urls: List[str]) -> List[str]:
    company_urls = list(set(["/".join(link.split("/")[:4]) for link in greenhouse_job_urls]))
    return company_urls

def lambda_handler(event, context):

    search_term = event.get("search_term","data scientist")
    logger.info(f"Searching DDG for {search_term}")
    links = ddg_search(search_term=search_term)
    greenhouse_company_urls = greenhouse_job_urls_to_company_urls(links)
    s3_keys = [f'deduped/{k.removeprefix("https://")}/dummy' for k in greenhouse_company_urls]


    return {'statusCode': 200, 's3_keys': s3_keys, 'num_companies': len(greenhouse_company_urls)}