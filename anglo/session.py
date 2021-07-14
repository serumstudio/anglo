#               Copyright (c) 2021 Serum Studio,
#
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

# This modue handles the main session and caching system for anglo.

from anglo.middleware import SessionMiddleware
from typing import Callable
from typing import Any

class Session:
    """
    A session wrapper for SessionMiddleware.
    
    Example Session:

        >>> app = Anglo(__name__)
        >>> session = Session(app)
        >>> ...
        >>> @app.route('/')
        >>> def home(request):
        >>>     if 'username' in session:
        >>>         username = session['username']
        >>>         return 'Logged in as {}'.format(username)
        >>>     else:
        >>>         return 'You're not yet logged in!' 
    
    Parameters:

    """

    #: Initialize a dictionary of session option for the session.
    session_option = {}

    #: The environ key to be used.
    session_env    = 'anglo.session'

    #: Middleware to be used.
    __middleware   = SessionMiddleware


    def __init__(self, app: Callable[..., Any] = None):
        
        if app == None:
            raise ValueError("app can't be a NoneType")

        #: Set the app parameter to a global variable
        self.app = app


    
