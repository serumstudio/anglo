
#               Copyright (c) 2021 Serum Studio.

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


# DIFFERENT TYPE OF ROUTERS
# From wheezy.routing

import re
from .utils import outer_split

RE_PLAIN_ROUTE  = re.compile(r"^[\w\./-]+$")
RE_CHOICE_ROUTE = ""
RE_SPLIT = re.compile(r"\<(\w+)\>")
RE_SPLIT_CURLY = re.compile(r"(?P<n>{[\w:]+.*?})")
RE_CHOICE_ROUTE = re.compile(
    r"^(?P<p>[\w/]*)" r"\{(?P<n>\w+):\((?P<c>[\w|]+)\)\}" r"(?P<s>[\w/]*)$"
)

patterns = {
    # one or more digits
    "i": r"\d+",
    "int": r"\d+",
    "number": r"\d+",
    "digits": r"\d+",
    # one or more word characters
    "w": r"\w+",
    "word": r"\w+",
    # everything until ``/``
    "s": r"[^/]+",
    "segment": r"[^/]+",
    "part": r"[^/]+",
    # any
    "*": r".+",
    "a": r".+",
    "any": r".+",
    "rest": r".+",
}

default_pattern = "s"

def convert(s):
    """
    Convert curly expression into regex with
    named groups.
    """
    parts = outer_split(s, sep="[]")
    parts[1::2] = ["(%s)?" % p for p in map(convert, parts[1::2])]
    parts[::2] = map(convert_single, parts[::2])
    return "".join(parts)


def convert_single(s):
    """
    Convert curly expression into regex with
    named groups.
    """
    parts = RE_SPLIT.split(s)
    return "".join(map(replace, parts))


def replace(val):
    """
    Replace `{group_name:pattern_name}` by regex with
    named groups.
    """
    if val.startswith("{") and val.endswith("}"):
        group_name, pattern_name = parse(val[1:-1])
        pattern = patterns.get(pattern_name, pattern_name)
        return "(?P<%s>%s)" % (group_name, pattern)
    return val


def parse(s):
    """
    Parse `s` according to `group_name:pattern_name`.
    There is just `group_name`, return default
    `pattern_name`.
    """
    if ":" in s:
        return tuple(s.split(":", 1))
    return s, default_pattern

def parse_pattern(pattern):
    """
    Returns path_format and names.
    """
    pattern = strip_optional(pattern)
    parts = outer_split(pattern, sep="()")
    if len(parts) % 2 == 1 and not parts[-1]:
        parts = parts[:-1]
    names = [RE_SPLIT.split(p)[1] for p in parts[1::2]]
    parts[1::2] = ["%%(%s)s" % p for p in names]
    return "".join(parts), names


def strip_optional(pattern):
    """
    Strip optional regex group flag.
    at the beginning
    """
    
    if ")?" not in pattern:
        return pattern
    parts = outer_split(pattern, sep="()")
    for i in range(2, len(parts), 2):
        part = parts[i]
        if part.startswith("?"):
            parts[i] = part[1:]
            parts[i - 1] = strip_optional(parts[i - 1])
        else:
            parts[i - 1] = "(%s)" % parts[i - 1]
    return "".join(parts)


def build_curly_route(pattern, finishing=True, kwargs=None, name=None):
    """Convert pattern expression into regex with
    named groups and create regex route.
    """
    if isinstance(pattern, RegexRoute):
        return pattern
    if RE_SPLIT_CURLY.search(pattern):
        return RegexRoute(convert(pattern), finishing, kwargs, name)

    return None


def build_plain_route(pattern, finishing=True, kwargs=None, name=None):
    """
    If the plain route regular expression match the pattern
    than create a Plain `:class:` instance.
    """
    if isinstance(pattern, PlainRoute):
        return pattern
    if pattern == "" or RE_PLAIN_ROUTE.match(pattern):
        return PlainRoute(pattern, finishing, kwargs, name)

    return None

def build_regex_route(pattern, finishing=True, kwargs=None, name=None):
    """
    There is no special tests to match regex selection
    strategy.
    """
    if isinstance(pattern, RegexRoute):
        return pattern
    return RegexRoute(pattern, finishing, kwargs, name)


def build_choice_route(pattern, finishing=True, kwargs=None, name=None):
    """If the choince route regular expression match the pattern
    than create a ChoiceRoute instance.
    """
    if isinstance(pattern, ChoiceRoute):
        return pattern
    m = RE_CHOICE_ROUTE.match(pattern)
    if m:
        return ChoiceRoute(pattern, finishing, kwargs, name)
    return None

route_builders = [ build_plain_route, build_regex_route, build_curly_route, build_choice_route ]


class RegexRoute:
    """
    A route based on regular expression.
    """

    exact_matches = None

    def __init__(self, pattern, finishing=True, kwargs=None, name=None):
        pattern = pattern.lstrip("^").rstrip("$")
        # Choose match strategy
        self.path_format, names = parse_pattern(pattern)
        if kwargs:
            self.kwargs = dict.fromkeys(names, "")
            self.kwargs.update(kwargs)
            if finishing:
                self.kwargs["route_name"] = name
            self.match = self.match_with_kwargs
            self.path = self.path_with_kwargs
            self.path_value = self.path_format % self.kwargs
        else:
            if finishing:
                self.name = name
                self.match = self.match_no_kwargs_finishing
            else:
                self.match = self.match_no_kwargs
            self.path = self.path_no_kwargs

        pattern = "^" + pattern
        if finishing:
            pattern = pattern + "$"
        self.regex = re.compile(pattern)

    def match_no_kwargs(self, path):
        """If the ``path`` match the regex pattern."""
        m = self.regex.match(path)
        if m:
            return m.end(), m.groupdict()
        return -1, None

    def match_no_kwargs_finishing(self, path):
        """If the ``path`` match the regex pattern."""
        m = self.regex.match(path)
        if m:
            kwargs = m.groupdict()
            kwargs["route_name"] = self.name
            return m.end(), kwargs
        return -1, None

    def match_with_kwargs(self, path):
        """If the ``path`` match the regex pattern."""
        m = self.regex.match(path)
        if m:
            kwargs = m.groupdict()
            return (m.end(), dict(self.kwargs, **kwargs))
        return -1, None

    def path_with_kwargs(self, values=None):
        """Build the path for the given route by substituting
        the named places of the regual expression.
        Specialization case: route was initialized with
        default kwargs.
        """
        if values:
            return self.path_format % dict(self.kwargs, **values)
        else:
            return self.path_value

    def path_no_kwargs(self, values):
        """Build the path for the given route by substituting
        the named places of the regual expression.
        Specialization case: route was initialized with
        no default kwargs.
        """
        return self.path_format % values



class ChoiceRoute:
    """
    Route based on choice match, e.g. {locale:(en|ru)}.
    """

    def __init__(self, pattern, finishing=True, kwargs=None, name=None):
        kwargs = kwargs and kwargs.copy() or {}
        if name:
            kwargs["route_name"] = name
        self.kwargs = kwargs
        m = RE_CHOICE_ROUTE.match(pattern)
        prefix, self.name, choice, suffix = m.groups()
        choices = choice.split("|")
        self.exact_matches = [
            (prefix + c + suffix, dict(kwargs, **{self.name: c}))
            for c in choices
        ]
        self.patterns = [(p, (len(p), kw)) for p, kw in self.exact_matches]
        self.path_format = prefix + "%s" + suffix

    def match(self, path):
        """
        If the `path` matches, return the end of
        substring matched and kwargs. Otherwise
        return `(-1, None)`.
        """

        for pattern, result in self.patterns:
            if path.startswith(pattern):
                return result
        return (-1, None)

    def path(self, values=None):
        """
        Build the path for given route.
        """

        if not values or self.name not in values:
            values = self.kwargs
        return self.path_format % values[self.name]

class PlainRoute:
    """
    A route based on a plain string.
    """

    def __init__(self, pattern, finishing, kwargs=None, name=None):
        """
        Initializes the route by given `pattern`. If
        `finishing`` is True than choose `equals_math`
        strategy
        """
        kwargs = kwargs and kwargs.copy() or {}
        self.pattern = pattern
        self.matched = len(pattern)
        # Choose match strategy
        if finishing:
            if name:
                kwargs["route_name"] = name
            self.match = self.equals_match
        else:
            self.match = self.startswith_match
        self.exact_matches = ((pattern, kwargs),)
        self.kwargs = kwargs

    def equals_match(self, path):
        """
        If the `path` exactly equals pattern string,
        return end index of substring matched and a copy
        of `self.kwargs`.
        """
        return (
            path == self.pattern and (self.matched, self.kwargs) or (-1, None)
        )

    def startswith_match(self, path):
        """
        If the `path` starts with pattern string, return
        the end of substring matched and `self.kwargs`.
        """
        return (
            path.startswith(self.pattern)
            and (self.matched, self.kwargs)
            or (-1, None)
        )

    def path(self, values=None):
        """
        Build the path for given route by simply returning
        the pattern used during initialization.
        """
        return self.pattern
