import asyncio
from adaptors import QueryableAdaptor
from model import OpenSearchColumn, OpenSearchIndex, QueryResponse
import httpx

OS_TO_SPARK_TYPES =  {
    "keyword": "string",
    "text": "string",
    "long": "long",
    "integer": "int",
    "short": "int",
    "byte": "int",
    "double": "double",
    "float": "float",
    "boolean": "boolean",
    "date": "timestamp",
}
SPARK_TO_OS_TYPES = {
    "string": "keyword",
    "long": "long",
    "int": "integer",
    "double": "double",
    "float": "float",
    "boolean": "boolean",
    "date": "date",
    "bigint": "long",
    "timestamp": "date"
}


class SparkAdaptor(QueryableAdaptor):
    def __init__(self, client: httpx.AsyncClient, url: str = "http://localhost:5000"):
        self.url = url
        self.client = client
        # Concurrency limit.
        self.request_sem = asyncio.Semaphore(24)

    async def create_index(self, index: OpenSearchIndex):
        schema = {
            col.name: OS_TO_SPARK_TYPES.get(col.dtype, "string") 
            for col in index.columns
        }
        
        async with self.request_sem:
            response = await self.client.post(
                f"{self.url}/load",
                json={
                    "table": index.name,
                    "schema": schema,
                    "data": index.documents
                }
            )
        response.raise_for_status()

    async def cleanup_index(self, index: OpenSearchIndex):
        async with self.request_sem:
            response = await self.client.post(
                f"{self.url}/drop",
                json={"table": index.name}
            )
        response.raise_for_status()

    async def run_query(self, query: str) -> QueryResponse:
        async with self.request_sem:
            response = await self.client.post(
                f"{self.url}/query",
                json={"query": query}
            )
        response.raise_for_status()
        data = response.json()
        
        columns = [
            OpenSearchColumn(name=name, dtype=SPARK_TO_OS_TYPES[dtype])
            for name, dtype in data["schema"].items()
        ]
        
        return QueryResponse(
            columns=columns,
            rows=data["result"]
        )

    async def close(self):
        await self.client.aclose()
