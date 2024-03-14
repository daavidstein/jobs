from scrape import dedupe_keys, clean_url, job_url_to_s3key

def test_dedupe_keys():

    existing_keys = ['deduped/boards.greenhouse.io/6sense/jobs/5567149',
     'deduped/boards.greenhouse.io/afresh/jobs/5017634004',
     'deduped/boards.greenhouse.io/alethea/jobs/5051094004',
     'deduped/boards.greenhouse.io/alma/jobs/7251555002',
     'deduped/boards.greenhouse.io/alpaca/jobs/5076561004',
     'deduped/boards.greenhouse.io/aperiatechnologies/jobs/5086449004',
    ]

    new_job_urls = ['https://boards.greenhouse.io/osmo/jobs/4313428006?gh_jid=4313428006',
 'https://boards.greenhouse.io/perplexityai/jobs/4231718007',
 'https://boards.greenhouse.io/podium81/jobs/5742900',
 'https://boards.greenhouse.io/point72/jobs/4644238002',
 'https://boards.greenhouse.io/remotasks/jobs/4352042005',
 'https://boards.greenhouse.io/rhombuspower/jobs/4890727003']

    cleaned_job_urls  = ['https://boards.greenhouse.io/osmo/jobs/4313428006',
 'https://boards.greenhouse.io/perplexityai/jobs/4231718007',
 'https://boards.greenhouse.io/podium81/jobs/5742900',
 'https://boards.greenhouse.io/point72/jobs/4644238002',
 'https://boards.greenhouse.io/remotasks/jobs/4352042005',
 'https://boards.greenhouse.io/rhombuspower/jobs/4890727003']

    job_dict = {k: {"key":"val"} for k in existing_keys + new_job_urls}

    deduped_jobs_dict = dedupe_keys(existing_keys=existing_keys, jobs=job_dict, prefix="deduped/")

    assert sorted(deduped_jobs_dict) == sorted(list(cleaned_job_urls))


def test_clean_url():
    """Remove query bit from some greenhouse urls like boards.greenhouse.io/6sense/jobs/5567149?gh_jid=5567149"""

    assert clean_url("https://boards.greenhouse.io/employer/jobs/1234/?someestuffhere") == "https://boards.greenhouse.io/employer/jobs/1234/"
    assert clean_url("boards.greenhouse.io/6sense/jobs/5567149?gh_jid=5567149") == "boards.greenhouse.io/6sense/jobs/5567149"

def test_job_url_to_s3key_strips_protocol():

    assert job_url_to_s3key("https://stuffhere.com") == "stuffhere.com"
    assert job_url_to_s3key("http://stuffhere.com") == "stuffhere.com"

def test_job_url_to_adds_prefix():

    assert job_url_to_s3key("http://stuffhere.com",new_prefix="deduped"
                            ) =="deduped/stuffhere.com"