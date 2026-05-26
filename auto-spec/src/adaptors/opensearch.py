import asyncio
import json

from opensearchpy import AsyncOpenSearch

from adaptors import QueryableAdaptor
from model import OpenSearchIndex, QueryResponse, OpenSearchColumn


class OpenSearchAdaptor(QueryableAdaptor):
    def __init__(self, client: AsyncOpenSearch):
        self.client = client
        # Concurrency limit. This can be increased but it seems to make overall throughput slower.
        self.request_sem = asyncio.Semaphore(24)

    async def _init_index_mapping(self, index: OpenSearchIndex):
        async with self.request_sem:
            result = await self.client.indices.create(
                index.name,
                index.mapping(),
                params={"timeout": 120},
            )
        assert not result.get("errors", None), f"failed to create index: {result}"

    async def _populate_index(self, index: OpenSearchIndex):
        header = json.dumps({"index": {"_index": index.name}})
        bulk_req = "\n".join(header + "\n" + json.dumps(doc) for doc in index.documents)
        async with self.request_sem:
            response = await self.client.bulk(
                bulk_req, params={"refresh": "true", "timeout": 120}
            )
        assert not response["errors"], f"failed to insert to index: {response}"

    async def create_index(self, index: OpenSearchIndex):
        await self._init_index_mapping(index)
        await self._populate_index(index)

    async def cleanup_index(self, index: OpenSearchIndex):
        async with self.request_sem:
            await self.client.indices.delete(index.name, params={"timeout": 120})

    async def run_query(self, query: str) -> QueryResponse:
        async with self.request_sem:
            response = await self.client.http.post(
                "/_plugins/_ppl", body={"query": query}, params={"timeout": 120}
            )

        columns = [OpenSearchColumn(s["name"], s["type"]) for s in response["schema"]]
        return QueryResponse(
            columns,
            [{c.name: v for c, v in zip(columns, row)} for row in response["datarows"]],
        )

    async def close(self):
        await self.client.close()
