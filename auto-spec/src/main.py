import httpx
from httpx import HTTPError
from adaptors import QueryableAdaptor
from adaptors.spark import SparkAdaptor
from data_generation.data import OPENSEARCH_DATA_TYPES
from data_generation.index import generate_index
from query_cases import TestCase

import asyncio
import json
import os
import sys
import typing

import tqdm
from opensearchpy import AsyncOpenSearch, OpenSearchException

from adaptors.context import context
from adaptors.opensearch import OpenSearchAdaptor
from report import generate_report


def opensearch() -> OpenSearchAdaptor:
    # TODO get this from a config instead of hardcoding it
    client = AsyncOpenSearch([{"host": "localhost", "port": 9200}])
    return OpenSearchAdaptor(client)


def expect_result_types(result: dict, expect_types: list[str]):
    types = list(map(lambda s: s.get("type", None), result.get("schema", [])))
    assert types == expect_types, f"incorrect types: {types}, expected {expect_types}"


def expect_result_data(result: dict, data: list[list[typing.Any]]):
    assert (
        result.get("datarows", []) == data
    ), f"incorrect data: {result}, expected {data}"


async def do_test(client: AsyncOpenSearch, test_case: TestCase):
    async with context(client, test_case.index()) as ctx:
        query = test_case.query.replace("$INDEX", ctx.index.name)
        return await ctx.run_query(query)


async def do_test_capturing_result(client: QueryableAdaptor, test_case: TestCase):
    result = {"case": test_case.to_case_dict(), "client": client.name()}
    try:
        result["body"] = (await do_test(client, test_case)).dict()
        result["result"] = "Success"
    except OpenSearchException as err:
        result["result"] = "Failure"
        result["err"] = str(err)
        result["err_source"] = "opensearch"
    except AssertionError as err:
        result["result"] = "Failure"
        result["err"] = str(err)
        result["err_source"] = "assertion"
    except HTTPError as err:
        result["result"] = "Failure"
        result["err"] = json.loads(err.response.text)
        result["err_source"] = "http"
    return result


def load_tests() -> typing.Generator[TestCase]:
    for dirpath, _, filenames in os.walk("src/query_cases/cases"):
        for filename in filenames:
            if not filename.endswith(".json"):
                continue
            with open(os.path.join(dirpath, filename), "r") as fp:
                yield TestCase.from_case_dict(filename, json.load(fp))


async def main_run_tests():
    tests = list(load_tests())
    # Filter out JOIN queries as we don't currently have multi-index loading
    tests = [t for t in tests if 'command:join' not in t.tags]

    spark_adaptor = SparkAdaptor(httpx.AsyncClient(timeout=60))
    os_adaptor = opensearch()
    try:
        futures = [
            asyncio.create_task(do_test_capturing_result(os_adaptor, test_case))
            for test_case in tests
        ]
        futures.extend([
            asyncio.create_task(do_test_capturing_result(spark_adaptor, test_case))
            for test_case in tests
        ])
        results = []
        for future in tqdm.tqdm(
            asyncio.as_completed(futures),
            total=len(futures),
        ):
            result = await future
            results.append(result)
        generate_report(results)
    finally:
        await os_adaptor.close()
        await spark_adaptor.close()


# TODO modularize
def build_case_from(function, signature, sig_idx):
    if not all(s in OPENSEARCH_DATA_TYPES for s in signature):
        return
    index = generate_index(column_types=signature)
    if function["inline"]:
        insert = f" {function['str'].upper()} "
        query = f"source = $INDEX | eval result = ({insert.join(col.name for col in index.columns)}) | fields result"
    else:
        query = f"source = $INDEX | eval result = {function['str']}({', '.join(col.name for col in index.columns)}) | fields result"

    case = {
        "data": {
            "mapping": {col.name: col.dtype for col in index.columns},
            "documents": index.documents,
        },
        "query": {
            "language": "ppl",
            "query": query,
        },
    }

    with open(f"src/query_cases/cases/{function['name']}_{sig_idx}.json", "w") as fp:
        json.dump(case, fp, indent=4)


def main_generate_tests():
    with open("data/function_signatures.json", "r") as fp:
        functions = json.load(fp)
    for function in functions:
        for i, signature in enumerate(function["signatures"]):
            build_case_from(function, signature, i)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: main.py [test|generate]")
        sys.exit(1)
    if sys.argv[1] == "test":
        asyncio.run(main_run_tests())
    if sys.argv[1] == "generate":
        main_generate_tests()
