import random
import uuid


from model import OpenSearchIndex, OpenSearchColumn
from data_generation.data import OPENSEARCH_DATA_TYPES, gen_column_name


def index_name():
    return "autospec_" + str(uuid.uuid4()).replace("-", "_")[19:]


def generate_index(column_types=None, document_count=None) -> OpenSearchIndex:
    if column_types is None:
        column_count = random.randint(1, 10)
        columns = [
            OpenSearchColumn(
                gen_column_name(), random.choice(list(OPENSEARCH_DATA_TYPES))
            )
            for _ in range(column_count)
        ]
    else:
        columns = [
            OpenSearchColumn(
                gen_column_name(),
                ctype if ctype != "any" else random.choice(list(OPENSEARCH_DATA_TYPES)),
            )
            for ctype in column_types
        ]

    if document_count is None:
        document_count = 10

    for column in columns:
        if column.dtype == "any":
            column.dtype = random.choice(list(OPENSEARCH_DATA_TYPES))

    documents = [
        {column.name: OPENSEARCH_DATA_TYPES[column.dtype]() for column in columns}
        for _ in range(document_count)
    ]
    return OpenSearchIndex(index_name(), columns, documents)
