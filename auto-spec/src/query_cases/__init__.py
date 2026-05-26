from dataclasses import dataclass

from model import OpenSearchColumn, OpenSearchIndex
from data_generation.index import index_name


@dataclass(init=True)
class TestCase:
    name: str
    mapping: dict[str, str]
    documents: list[dict]
    language: str
    query: str
    tags: list[str]

    def to_case_dict(self):
        return {
            "name": self.name,
            "data": {
                "mapping": self.mapping,
                "documents": self.documents,
            },
            "query": {
                "language": self.language,
                "query": self.query,
                "tags": self.tags
            }
        }

    def from_case_dict(case_name: str, case_dict: dict):
        return TestCase(
            case_name,
            case_dict["data"]["mapping"],
            case_dict["data"]["documents"],
            case_dict["query"]["language"],
            case_dict["query"]["query"],
            case_dict["query"].get("tags", [])
        )

    def index(self):
        return OpenSearchIndex(
            index_name(),
            [OpenSearchColumn(k, v) for k, v in self.mapping.items()],
            self.documents,
        )
