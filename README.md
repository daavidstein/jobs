# Jobs
This is a collection of utilities for scraping job descriptions from the web.
```
.
├── aws_lambda #lambda components of state machines
│   ├── crawl_companies #crawl-scrape-v2 
│   │   ├── crawl_companies.py
│   │   ├── dockerfile
│   │   ├── requirements.in
│   │   ├── requirements.txt
│   │   └── update_image.sh
│   ├── create_new_lambda.sh
│   ├── ddg_search #ddg-search 
│   │   ├── ddg_search.py
│   │   ├── dockerfile
│   │   ├── requirements.txt
│   │   └── update_image.sh
│   ├── put_objects_s3 #ddg-search
│   │   ├── dockerfile
│   │   ├── put_objects_s3.py
│   │   ├── requirements.txt
│   │   └── update_image.sh
│   ├── scrape_jds #crawl-scrape-v2
│   │   ├── dockerfile
│   │   ├── requirements.txt
│   │   ├── scrape_jds.py
│   │   └── update_image.sh
│   └── update_lambda.sh #template called by each update_image.sh above
├── make_dummy_company.sh #make empty placeholder files on s3 used for filtering in crawl-scrape-v2
├── README.md
├── requirements.in
├── requirements.txt
├── scrape.py
├── state_machines
│   ├── crawl-scrape-v2.asl.yaml
│   └── ddgsearch.yaml
├── tests.py
```

There are two AWS state machines: `ddg_search`  performs DuckDuckGo searches (right now only for jobs posted on Greenhouse ATS), and keeps track of companies which post those jobs on S3.

![Image](state_machines/ddg-search.png)

The `crawl-scrape` state machine lists companies in the S3 bucket, fetches all the job posting urls from the company job boards, and then performs a map step which scrapes all the job metadata asynchronously. This is also stored on an S3 Bucket for later analysis.

![Image](state_machines/crawl-scrape-v2.png)

# Updating lambda functions
The lambdas sometimes require updating. For instance, if a new version of dependency is released, the `requirements.txt` for that lambda may need to be updated. After making changes, run the shell script `update_image.sh` in the lambda directory in this repo. This will execute the shell script in `aws_lambda/update_lambda.sh` to update the specified lambda.

__TODO__ automate dependency updates for ddg-search.

I am currently working on utilities to filter the jobs on S3 by criteria such as title, location and perform alerting via AWS SNS

After that I'm planning on training some ML models on the job descriptions in order to rank them by relevance to a candidate's resume.