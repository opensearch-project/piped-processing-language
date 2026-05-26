import pandas as pd
import os
from tqdm import tqdm
import json
import re
from datetime import datetime
import ipaddress

# This assumes you've cloned it to `repos/` locally. If you want, update to the absolute path of
# your Spark clone. The directories here are e.g.
# https://github.com/opensearch-project/opensearch-spark/tree/main/e2e-test/src/test/resources/spark/queries/ppl.
SPARK_TABLES_DIR = 'repos/opensearch-spark/e2e-test/src/test/resources/spark/tables'
SPARK_PPL_TEST_DIR = 'repos/opensearch-spark/e2e-test/src/test/resources/spark/queries/ppl'
OUTPUT_DIR = 'src/query_cases/cases'

def load_indices():
    indices = {}
    for dirpath, _, filenames in os.walk(SPARK_TABLES_DIR):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            indices[filename] = pd.read_parquet(path)
    return indices

def load_ppl(path):
    with open(path, 'r') as fp:
        content = fp.read()
    # Clear comments
    content = re.sub(r'/\*[\s\S]*\*/', '', content)
    content = ''.join(l for l in content.splitlines() if not l.startswith('//'))
    content = content.strip()
    return content

def load_results(path):
    return pd.read_csv(path)

def load_tests():
    ppl, results = {}, {}
    for dirpath, _, filenames in os.walk(SPARK_PPL_TEST_DIR):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            if filename.endswith('.ppl'):
                ppl[filename.removesuffix('.ppl')] = load_ppl(path)
            elif filename.endswith('.results'):
                results[filename.removesuffix('.results')] = load_results(path)
    return ppl, results

def get_dataset_name(query):
    # Extract dataset name from query that starts with "source = dev.default."
    match = re.search(r'source\s*=\s*(?:dev\.default\.)?(\w+)', query, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Query doesn't match expected format: {query}")
    return f"{match.group(1)}.parquet"

def replace_dataset_name(query):
    # Extract dataset name from query that starts with "source = dev.default."
    query = re.sub(r'(source\s*=\s*)((dev\.default\.)?\w+)', r"\1$INDEX", query, flags=re.IGNORECASE)
    return query

def clear_timestamps(doc):
    dt_iso = lambda dt: dt.isoformat() if isinstance(dt, datetime) else dt
    doc = json.loads(json.dumps(doc, default=dt_iso))
    return doc

def is_ip_field(series):
    # Check first non-null value if it's an IP address
    sample = series.dropna().iloc[0] if not series.empty else None
    if not isinstance(sample, str):
        return False
    try:
        ipaddress.ip_address(sample)
        return True
    except ValueError:
        return False

def build_mapping(df):
    mapping = {}
    for column in df.columns:
        dtype = str(df[column].dtype)
        if 'int' in dtype:
            mapping[column] = 'integer'
        elif 'float' in dtype:
            mapping[column] = 'double'
        elif 'bool' in dtype:
            mapping[column] = 'boolean'
        elif 'datetime' in dtype:
            mapping[column] = 'date'
        elif 'string' in dtype:
            if is_ip_field(df[column]):
                mapping[column] = 'ip'
            else:
                mapping[column] = 'text'
        elif 'array' in dtype or 'list' in dtype:
            # You might want to determine the array element type
            mapping[column] = 'array'
        elif 'dict' in dtype or 'struct' in dtype or 'object' in dtype:
            mapping[column] = 'object'
        else:
            mapping[column] = 'text'
            
    return mapping


def create_test_case(query, df):
    mapping = build_mapping(df)

    # Convert DataFrame to list of dictionaries for documents
    documents = df.head(10).to_dict('records')
    documents = clear_timestamps(documents)

    # Create the full test case structure
    test_case = {
        "data": {
            "mapping": mapping,
            "documents": documents
        },
        "query": {
            "language": "ppl",
            "query": query
        }
    }
    return test_case

def generate_test_cases(indices, ppl, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    success_count, total_count = 0, len(ppl)

    for test_name, query in tqdm(ppl.items()):
        try:
            # Get the dataset name from the query
            dataset_name = get_dataset_name(query)
            query = replace_dataset_name(query)
            
            # Get the corresponding DataFrame
            if dataset_name not in indices:
                print(f"Warning: Dataset {dataset_name} not found for test {test_name}")
                continue
            
            df = indices[dataset_name]
            
            # Create the test case
            test_case = create_test_case(query, df)
            
            # Write to file
            output_path = os.path.join(output_dir, f"{test_name}.json")
            with open(output_path, 'w') as fp:
                json.dump(test_case, fp, indent=4)
            success_count += 1
                
        except ValueError as e:
            print(f"Error processing {test_name}: {str(e)}")
        except Exception as e:
            print(f"Unexpected error processing {test_name}: {str(e)}")
    return success_count, total_count

if __name__ == "__main__":
    indices = load_indices()
    ppl, results = load_tests()
    s, t = generate_test_cases(indices, ppl, OUTPUT_DIR)
    print(f"{s} / {t} tests successfully imported")
