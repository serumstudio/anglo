
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

from typing import Optional
from anglo.constants import HTTP_STATUS_CODES

def redirect():
    """
    A redirect function for the application.
    """

    pass


class BaseResponse:
    """
    A base class for the response.

    """

    def __init__(self, response=None, status=None, charset=None, content_type=None):

        if response is None:
            self.response = []
        
        elif isinstance(response, (str, bytes)):
            self.response = [response]

        else:
            self.response = response
        
        
        self.charset = charset
        self._status  = status
        self.content_type = content_type

    def __iter__(self):
        
        for k in self.response:
            if isinstance(k, bytes):
                yield k

            else:
                yield k.encode(self.charset)


class HttpResponse(BaseResponse):
    """
    A http response wrapper for `:class:` BaseResponse

    Example:
        
        >>> @app.route("/")
        >>> def home(request):
        >>>     return HttpResponse("<h3>Hello World!</h3>")
    
    Parameters:
        response (str):
            The response body.

        status (int):
            The status code to be sent. Usually 200 (OK)

        charset (str):
            The charset for the response header

    """

    #: The content type for the response.
    #: It should be text/html and cannot be changed.
    __content_type = "text/html"

    def __init__(self, response: Optional[str] = "", 
                status: Optional[int] = 200, charset: Optional[str] = "utf-8"):
        
        super(BaseResponse, self).__init__(response=response, 
                status=status, charset=charset, content_type=self.__content_type)

    @property
    def status(self):
        status_str = HTTP_STATUS_CODES[self._status]
        return f"{self._status} {status_str}"



class JsonResponse(BaseResponse):
    """
    A json response wrapper for `:class:` BaseResponse

    Example:
        
        >>> @app.route("/")
        >>> def api(request):
        >>>     return JsonResponse({ "method": request.method, 
        >>>             "message": "Simple JSON Response!" })
    
    Parameters:
        response (str):
            The response body.

        status (int):
            The status code to be sent. Usually 200 (OK)

        charset (str):
            The charset for the response header
    """

    __content_type = "text/json"

    def __init__(self, response: Optional[dict] = {}, 
                status: Optional[int] = 200, charset: Optional[str] = "utf-8"):
        
        super(BaseResponse, self).__init__(response=response, 
                status=status, charset=charset, content_type=self.__content_type)

