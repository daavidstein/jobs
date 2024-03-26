
from typing import List

from duckduckgo_search import DDGS
from logging import getLogger

logger = getLogger(__name__)
logger.setLevel("INFO")

def ddg_search(search_term: str= "data scientist", site:str= "boards.greenhouse.io", max_results:int=100) -> List[str]:

    with DDGS() as ddgs:
        links = [r["href"] for r in ddgs.text(f"{search_term} site:{site}", max_results=max_results)]

    return links

def greenhouse_job_urls_to_company_urls(greenhouse_job_urls: List[str]) -> List[str]:
    company_urls = list(set(["/".join(link.split("/")[:4]) for link in greenhouse_job_urls]))
    return company_urls

# def write_data_to_s3(data: dict, search_term: str, bucket_name: str = "scrapedjobs", client=None):
#     client = client or boto3.client("s3")
#
#     timestamp = int(time_ns())
#     key = f"{timestamp}/{search_term.replace(' ', '_')}.json"
#
#     client.put_object(
#         Body=json.dumps(data),
#         Bucket=bucket_name,
#         Key=key
#     )
#     return f"s3://{bucket_name}/{key}"

def lambda_handler(event, context):

    search_term = event.get("search_term","data scientist")
    links = ddg_search(search_term=search_term)
    greenhouse_company_urls = greenhouse_job_urls_to_company_urls(links)
    s3_keys = [f'deduped/{k.removeprefix("https://")}/dummy' for k in greenhouse_company_urls]
    # data = [get_job_data(job_url) for job_url in tqdm(links)]
    # data_json = {url: d for url, d in zip(links, data) if data}
    # s3_url = write_data_to_s3(data=data_json,search_term=search_term)
    # logger.info(f"{len(data_json)} jobs data written to {s3_url}")



    return {'statusCode': 200, 's3_keys': s3_keys, 'num_companies': len(greenhouse_company_urls)}