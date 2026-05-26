import asyncio
import copy
from collections import defaultdict
from contextlib import asynccontextmanager

from adaptors import QueryableAdaptor
from data_generation.index import OpenSearchIndex, index_name

# Enables a per-adaptor limit on the number of contexts that can exist at once. This helps avoid
# runaway resource usage by trying to run thousand of tests at once.
_context_pool = defaultdict(lambda: asyncio.Semaphore(128))


class QueryContext:
    def __init__(self, adaptor: QueryableAdaptor, index: OpenSearchIndex):
        self.adaptor = adaptor
        self.index = index

    async def run_query(self, query: str):
        return await self.adaptor.run_query(query)


@asynccontextmanager
async def context(adaptor: QueryableAdaptor, index: OpenSearchIndex):
    local_index = copy.copy(index) # Allow multiple contexts for the same index to exist in parallel
    local_index.name = index_name()

    async with _context_pool[id(adaptor)]:
        await adaptor.create_index(local_index)
        try:
            yield QueryContext(adaptor, local_index)
        finally:
            await adaptor.cleanup_index(local_index)
