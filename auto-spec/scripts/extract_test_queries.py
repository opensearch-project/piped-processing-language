import os
import json

queries = {}
for dirpath, _, filenames in os.walk('src/query_cases/cases'):
    for filename in filenames:
        path = os.path.join(dirpath, filename)
        with open(path, 'r') as fp:
            test = json.load(fp)
        queries[filename] = test['query']['query']

print(json.dumps(queries, indent=2, sort_keys=True))
