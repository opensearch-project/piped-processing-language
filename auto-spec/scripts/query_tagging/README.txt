To get useful statistics over all the queries, it's a good idea to have tags for all the queries
describing what they use. Tagging all the queries by hand would be a mess. This directory has:

1. All the queries at the time of writing in `queries.json`
2. I bulk-fed the queries to an LLM and asked it for tags, this results in `query_tags.json`
3. Then I re-fed that into another LLM to ask it to spot any inconsistencies, the output is `corrections.json`
4. The `attach_tags.py` script combines all this and adds it to the different query files.

Disclaimer: These have not been carefully hand-checked, there's 266 queries. I looked over a few and
the outputs seem "good enough."
