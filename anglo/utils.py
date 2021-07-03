
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


import sys
import os
from typing import ( Any, Callable, Dict, Iterable, 
        List, Optional, Protocol, Tuple
)

months = (None, "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

weekdays = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


class StartResponse(Protocol):
    def __call__(
        self, status: str, headers: List[Tuple[str, str]], exc_info: Optional[None] = ...
    ) -> Callable[[bytes], Any]: ...

WSGIEnvironment = Dict[str, Any]  # stable
WSGIApplication = Callable[[WSGIEnvironment, StartResponse], Iterable[bytes]]  # stable

def get_root_path(import_name: str) -> str:
    """
    Find the root path for the module.

    Argument:
        import_name (str):
            The name of the module to get the root path.
    """

    module = sys.modules.get(import_name)

    if module is not None and hasattr(module, "__file__"):
        return os.path.dirname(os.path.realpath(module.__file__))

def to_bytes(string, encoding='utf-8'):
    """
    Convert text to bytes
    """
    if isinstance(string, bytes):
        return string

    elif isinstance(string, str):
        return string.encode(encoding)

    else:
        return bytes(string)    
