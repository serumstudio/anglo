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


class Request:
    """
    
    A request wrapper for the application. 
    This class cannot be used directly. It was parsed by the application.

    Example:
       
        >>> app = Anglo(__name__)
        >>> @app.route('/')
        >>> def home(request): # -> Here is the request that was passed by the application.
        >>>     print(request)
        >>>     return "Home Page"

    Parameters:

        environ(dict): 
            A environment variables of the app.
            
    """

    #: The query args of the request.
    __args: dict = {}

    def __init__(self, environ: dict):
        self.env = environ


    @property
    def args(self):

        return self.__args
