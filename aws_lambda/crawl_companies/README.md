# crawl_companies   

- This lambda function is used in the map step of the `crawl-scrape-v2` state machine
- It precedes the lambda `scrape-jds` in that map step.
- This lambda fetches all the job posting urls from a company's job board

![Image](../../state_machines/crawl-scrape-v2.png)
