
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
from typing import Callable
from typing import Any 
from anglo.utils import get_root_path
from anglo.routing import Router

class Anglo:
    """
    This `:class:` implements WSGI application that holds
    routing, session, middlewares and more.
    """

    #: The main router for the app
    __router = Router()

    def __init__(self, name: str,
            static_folder: Optional[str] = "static",
            static_url_path: Optional[str] = "/static",
            template_folder: Optional[str] = "templates"):

        
        #: The name of the package to be imported 
        #: this is required in order for the debugger to work.
        self.name               = name


        #: The main root path of the imported package
        #: This path is used for the debugger and other purposes
        self.root_path          = get_root_path(self.name)
        

        #: Static folder for the application.
        #: *Optional; And the default value is static
        self.static_folder      = static_folder


        #: Static url path to be served for the application
        #: *Optional; The default value is /static.
        self.static_url_path    = static_url_path


        #: Template folder for the application
        #: *Optional; The default value is templates
        self.template_folder    = template_folder


    def route(self, path: str, 
            name: Optional[str] = None, 
            _func: Callable[..., Any] = None, **options):
        

        """
        A route decorator that binds function to the wsgi application.

        Example:

            >>> @app.route('/')
            >>> def homepage(request):
            >>>     return "Hello World!"

        Parameters:
            path (str):
                A route path to be used.

            name (str):
                The name of the router. [Optional]

            _func (function):
                The main wrapper / function for the decorator.

            options (kwargs):
                Additional options for the router.
        
        """

        if callable(path): path, _func = None, path

        def deco(_func):
            self.__router.add_route(path, _func, name, options)

            return deco


        return deco(_func) if _func else deco


    def __call__(self, environ, start_response):
        handler, _ = self.__router.match(environ['PATH_INFO'])

        if handler == None:
            start_response("404 Not Found", [('Content-Type', 'text/html')])
            return [b"404 Not Found"]

        else:
            return handler(environ, start_response)
        
