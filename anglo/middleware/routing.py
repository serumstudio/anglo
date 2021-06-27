

import re

RE_STRIP_NAME = re.compile(r"(Handler|Controller|Page|View)$")
RE_CAMELCASE_TO_UNDERSCOPE_1 = re.compile("(.)([A-Z][a-z]+)")
RE_CAMELCASE_TO_UNDERSCOPE_2 = re.compile("([a-z0-9])([A-Z])")

class Route:
    """
    Route abstact `:class:`
    """

    def match(self, path):
        raise NotImplementedError()

    def path(self, value=None):
        raise NotImplementedError   


class Router:
    """
    
    """

    def __init__(self, r_builder=None):
        pass