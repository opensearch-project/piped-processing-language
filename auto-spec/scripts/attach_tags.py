import json
import os

def load_json_file(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)

def attach_tags():
    tags_file = 'scripts/query_tagging/query_tags.json'
    query_tags = load_json_file(tags_file)
    
    corrections_file = 'scripts/query_tagging/corrections.json'
    corrections = load_json_file(corrections_file)
    
    for query_id, correction in corrections.items():
        if query_id in query_tags:
            query_tags[query_id].extend(correction.get('add', []))
            query_tags[query_id] = list(dict.fromkeys(query_tags[query_id]))

    cases_dir = 'src/query_cases/cases'
    
    for query_file in query_tags.keys():
        case_file_path = os.path.join(cases_dir, query_file)
        
        if not os.path.exists(case_file_path):
            print(f"Warning: Case file not found: {query_file}")
            continue
            
        try:
            case_data = load_json_file(case_file_path)
            case_data['query']['tags'] = query_tags[query_file]
            save_json_file(case_file_path, case_data)
            
        except Exception as e:
            print(f"Error processing {query_file}: {str(e)}")

if __name__ == "__main__":
    attach_tags()
