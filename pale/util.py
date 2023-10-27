import re

SPACE_TEMPLATE = re.compile(r'\s+')
SPACE = ' '
NON_ALPHANUMERIC = re.compile(r'[^\w]+')
NON_ALPHANUMERIC_OR_SPACE = re.compile(r'[^\w\s]+')


def normalize(string: str):
    return SPACE_TEMPLATE.sub(SPACE, string).strip()


def to_kebab_case(string: str):
    return SPACE_TEMPLATE.sub('-', string).lower()


def drop_non_alphanumeric(string: str):
    try:
        return NON_ALPHANUMERIC.sub('', string)
    except Exception:
        return string


def drop_non_alphanumeric_or_space(string: str):
    try:
        return NON_ALPHANUMERIC_OR_SPACE.sub('', string)
    except Exception:
        return string
