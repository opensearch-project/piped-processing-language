from dataclasses import dataclass
import typing


@dataclass(init=True)
class OpenSearchColumn:
    name: str
    dtype: str

    def mapping_obj(self):
        return {"type": self.dtype}


@dataclass(init=True)
class OpenSearchIndex:
    name: str
    columns: list[OpenSearchColumn]
    documents: list[dict[str, typing.Any]]

    def mapping(self):
        properties = {c.name: c.mapping_obj() for c in self.columns}
        return {
            "settings": {
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                }
            },
            "mappings": {"properties": properties},
        }


@dataclass(init=True)
class QueryResponse:
    columns: list[OpenSearchColumn]
    rows: list[dict[str, typing.Any]]

    def dict(self):
        return {
            "columns": { c.name: c.dtype for c in self.columns },
            "rows": self.rows
        }
