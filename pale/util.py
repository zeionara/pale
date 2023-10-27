import re

SPACE_TEMPLATE = re.compile(r'\s+')
SPACE = ' '
NON_ALPHANUMERIC = re.compile(r'[^\w]+')


def normalize(string: str):
    return SPACE_TEMPLATE.sub(SPACE, string).strip()


def to_kebab_case(string: str):
    return SPACE_TEMPLATE.sub('-', string).lower()


def drop_non_alphanumeric(string: str):
    return NON_ALPHANUMERIC.sub('', string)
