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

# This modue handles the middleware for sessions using `beaker`.
# The code are from beaker:
# https://github.com/bbangert/beaker/blob/master/beaker/middleware.py



from beaker.session import Session, SessionObject
from beaker.util import coerce_session_params
import warnings

beaker_session = None


class SessionMiddleware(object):
    session = beaker_session

    def __init__(self, wrap_app, config=None, environ_key='beaker.session',
                 **kwargs):
        
        """Initialize the Session Middleware
        The Session middleware will make a lazy session instance
        available every request under the ``environ['beaker.session']``
        key by default. The location in environ can be changed by
        setting ``environ_key``.
        ``config``
            dict  All settings should be prefixed by 'session.'. This
            method of passing variables is intended for Paste and other
            setups that accumulate multiple component settings in a
            single dictionary. If config contains *no session. prefixed
            args*, then *all* of the config options will be used to
            intialize the Session objects.
        ``environ_key``
            Location where the Session instance will keyed in the WSGI
            environ
        ``**kwargs``
            All keyword arguments are assumed to be session settings and
            will override any settings found in ``config``
        """
        config = config or {}

        # Load up the default params
        self.options = dict(invalidate_corrupt=True, type=None,
                            data_dir=None, key='beaker.session.id',
                            timeout=None, save_accessed_time=True, secret=None,
                            log_file=None)

        # Pull out any config args meant for beaker session. if there are any
        for dct in [config, kwargs]:
            for key, val in dct.items():
                if key.startswith('beaker.session.'):
                    self.options[key[15:]] = val
                if key.startswith('session.'):
                    self.options[key[8:]] = val
                if key.startswith('session_'):
                    warnings.warn('Session options should start with session. '
                                  'instead of session_.', DeprecationWarning, 2)
                    self.options[key[8:]] = val

        # Coerce and validate session params
        coerce_session_params(self.options)

        # Assume all keys are intended for session if none are prefixed with
        # 'session.'
        if not self.options and config:
            self.options = config

        self.options.update(kwargs)
        self.wrap_app = self.app = wrap_app
        self.environ_key = environ_key

    def __call__(self, environ, start_response):
        session = SessionObject(environ, **self.options)
        if environ.get('paste.registry'):
            if environ['paste.registry'].reglist:
                environ['paste.registry'].register(self.session, session)
        environ[self.environ_key] = session
        environ['beaker.get_session'] = self._get_session

        if 'paste.testing_variables' in environ and 'webtest_varname' in self.options:
            environ['paste.testing_variables'][self.options['webtest_varname']] = session

        def session_start_response(status, headers, exc_info=None):
            if session.accessed():
                session.persist()
                if session.__dict__['_headers']['set_cookie']:
                    cookie = session.__dict__['_headers']['cookie_out']
                    if cookie:
                        headers.append(('Set-cookie', cookie))
            return start_response(status, headers, exc_info)
        return self.wrap_app(environ, session_start_response)

    def _get_session(self):
        return Session({}, use_cookies=False, **self.options)
