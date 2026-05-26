import json
from collections import defaultdict

def group_by_name(results):
    grouped_by_name = defaultdict(lambda: [])
    for result in results:
        grouped_by_name[result['case']['name']].append(result)
    for v in grouped_by_name.values():
        v.sort(key=lambda x: x['client'])
    return grouped_by_name


def build_comparative_report(results):
    results = group_by_name(results)
    for key, values in sorted(results.items()):
        opensearch, spark = values[0], values[1]
        os_success, spark_success = opensearch['result'] == 'Success', spark['result'] == 'Success'
        if os_success and spark_success:
            d_type_agree = opensearch['body']['columns'] == spark['body']['columns']
            content_agree = opensearch['body']['rows'] == spark['body']['rows']
            yield {
                'key': key,
                'tags': values[0]['case']['query']['tags'],
                'opensearch': os_success,
                'spark': spark_success,
                'results_match': opensearch['result'] == spark['result'],
                'dtype_match': d_type_agree,
                'content_match': content_agree,
            }
        else:
            yield {
                'key': key,
                'tags': values[0]['case']['query']['tags'],
                'opensearch': os_success,
                'spark': spark_success,
                'results_match': opensearch['result'] == spark['result']
            }


def analyze_by_tag(comparative_results):
    tag_stats = {}
    
    for result in comparative_results:
        for tag in result['tags']:
            if tag not in tag_stats:
                tag_stats[tag] = {
                    'tag': tag,
                    'total': 0,
                    'opensearch_success': 0,
                    'spark_success': 0,
                    'results_match': 0,
                    'dtype_match': 0,
                    'content_match': 0
                }
            
            stats = tag_stats[tag]
            stats['total'] += 1
            
            if result['opensearch']:
                stats['opensearch_success'] += 1
            if result['spark']:
                stats['spark_success'] += 1
            if result['results_match']:
                stats['results_match'] += 1
            if 'dtype_match' in result and result['dtype_match']:
                stats['dtype_match'] += 1
            if 'content_match' in result and result['content_match']:
                stats['content_match'] += 1
    
    for tag, stats in tag_stats.items():
        total = stats['total']
        for key in stats:
            if isinstance(stats[key], str):
                continue
            if key != 'total':
                stats[key] = (stats[key] / total) * 100
                
    return tag_stats


def generate_report(results):
    raw_results = list(build_comparative_report(results))
    tag_aggregate = analyze_by_tag(raw_results)

    with open('test_report.jsonl', 'w') as fp:
        for v in sorted(tag_aggregate.values(), key=lambda x: x['tag']):
            v['line_type'] = 'tag'
            print(json.dumps(v), file=fp)
        for v in sorted(raw_results, key=lambda x: x['key']):
            v['line_type'] = 'query'
            print(json.dumps(v), file=fp)
