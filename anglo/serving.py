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

# This modue handles serving the application with different server adapters

from typing import Optional
import os


SERVER_ADAPTERS = [ "gunicorn", "waitress", "anglo", "paste" ]

class Serving:
    """
    A class for serving WSGI Applications / Anglo Applications.

    Parameters:
        
        host (str):
            The host to server to serve. Returns '' which accepts all network gateway interface
        
        port (int): 
            The given port for the server. Return 3000 if None.
        
        debug (bool):
            Set if debugging is true or not.

        adapter (str):
            The given adapter for the server to serve. Return the common server which is
            the AngloServer
    """

    def __init__(self, host: Optional[str] = "",
                port: Optional[int] = 3000, debug: bool = True,
                adapter: str = "anglo", **options):

        #: The host of the server to serve. Return "" which accept all network gateway interface
        self.host   = host 

        #: The port of the server to serve.
        #: You can define it as well via environment variables with SERVER_PORT
        self.port   = port or os.environ["SERVER_PORT"]

        #: Set the debugger to True or False.
        #: Default value: True
        self.debug  = debug

        #: The server adapter to serve. Return defaut AngloServer if none.
        #: You can define it as well via environment variables with SERVER_ADAPTER
        self.adapter = adapter or os.environ["SERVER_ADAPTER"]

        #: Check if the server adapter exist
        if self.adapter not in SERVER_ADAPTERS:
            raise ValueError("There are no `{}` server adapters.".format(SERVER_ADAPTERS))

        #: Check if debug is True
        if self.debug:
            pass


class ServerAdapter:
    """
    Base class for server adapters.

    Parameters:
        host (str):
            Host of the server
        
        port(str):
            Port of the server

        options(kwargs):
            Some options used for some adapters.
    """

    def __init__(self, host: Optional[str] = "",
            port: Optional[int] = 3000, **options):

        self.host       = host
        self.port       = port
        self.options    = options

    def run(self, app):
        pass


class GunicornServer(ServerAdapter):
    """
    A gunicorn server adapter.
    
    """

    def run(self, app):
        from gunicorn.app.base import BaseApplication

        if self.host.startswith("unix:"):
            config = {'bind': self.host}

        else:
            config = {'bind': "%s:%d" % (self.host, self.port)}
        
        config.update(self.options)

        class GunicornApplication(BaseApplication):
            def load_config(self):
                for key, value in config.items():
                    self.cfg.set(key, value)

            def load(self):
                return app

        GunicornApplication().run()

class WaitressServer(ServerAdapter):
    """
    A waitress server adapter.

    """

    def run(self, app):
        from waitress import serve

        serve(app, host=self.host, port=self.port, **self.options)

class PasteServer(ServerAdapter):
    """
    A paste server adapter.
    
    """    
    
    def run(self, app):
        from paste import httpserver
        from paste.translogger import TransLogger

        app = TransLogger(app, setup_console_handler=True)
        httpserver.serve(
            app, host=self.host, 
            port=self.port, **self.options
        )


class AngloServerAdapter(ServerAdapter):
    """
    A default Anglo Server used for debugging. Haven't tried on production yet.
    """

    def run(self, app):
        from anglo.server import AngloServer
        server = AngloServer(self.host, self.port, app)
        server.serve_forever()