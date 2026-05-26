import random

import faker

_fake = faker.Faker()


def gen_column_name():
    # prefix with col_ to avoid accidentally landing on any PPL grammar keywords
    return "col_" + gen_keyword().lower()


def gen_boolean():
    return random.choice((True, False))


def gen_byte():
    return random.randint(-128, 127)


def gen_int():
    return random.randint(-(2**31), 2**31 - 1)


def gen_keyword():
    global _fake
    return _fake.word()


def gen_long():
    return random.randint(-(2**63), 2**63 - 1)


def gen_short():
    return random.randint(-(2**15), 2**15 - 1)


def gen_text():
    global _fake
    return _fake.text()


# TODO: floats, dates, ip, binary, objects/nested
OPENSEARCH_DATA_TYPES = {
    "boolean": gen_boolean,
    "byte": gen_byte,
    "integer": gen_int,
    "keyword": gen_keyword,
    "long": gen_long,
    "short": gen_short,
    "text": gen_text,
}
