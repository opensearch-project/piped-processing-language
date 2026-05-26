from abc import ABC, abstractmethod

from model import OpenSearchIndex, QueryResponse


class QueryableAdaptor(ABC):
    """
    Used to support testing queries on multiple runtimes. One adaptor will be created per test suite
    and will be `close`d at the end. The adaptor is responsible for enforcing any concurrency
    limits, and for converting to/from the index and response types.
    """

    def name(self):
        """
        Human-readable identifier for the adaptor, to be rendered in test reports.
        """
        return type(self).__name__.removesuffix('Adaptor')

    @abstractmethod
    async def create_index(self, index: OpenSearchIndex):
        pass

    @abstractmethod
    async def cleanup_index(self, index: OpenSearchIndex):
        pass

    @abstractmethod
    async def run_query(self, query: str) -> QueryResponse:
        pass

    @abstractmethod
    async def close(self):
        """
        Final teardown operations for the Adaptor before program shutdown.
        """
        pass
