
import re

def outer_split(expression, sep="()"):
    """
    Splits given `expression` by outer most separators.
    >>> outer_split('123')
    ['123']
    >>> outer_split('123(45(67)89)123(45)67')
    ['123', '45(67)89', '123', '45', '67']
    If expression is not balanced raises ``ValueError``.
    >>> outer_split('123(') # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: ...
    """
    assert 2 == len(sep)
    start_sep, end_sep = sep
    start_count = end_count = 0
    parts = []
    part = ""
    for token in expression:
        if token == start_sep:
            if start_count == end_count:
                parts.append(part)
                part = ""
                start_count += 1
                continue
            start_count += 1
        elif token == end_sep:
            end_count += 1
            if start_count == end_count:
                parts.append(part)
                part = ""
                continue
        part += token
    if start_count != end_count:
        raise ValueError("Expression is not balanced")
    parts.append(part)
    return parts