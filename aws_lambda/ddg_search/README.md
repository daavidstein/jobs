# ddg_search

- This lambda function is used in the `ddg-search` state machine. 
- It precedes the lambda `put_objects_s3` in that state machine.
- The version of `duckduckgo_search` used in this lambda needs to be updated frequentliy, otherwise the state machine will likely fail.