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

# This modue handles the simple wsgi server used for debugging | development.


import socket
import urllib
import time
import sys
import io
import datetime
import typing as t
from anglo.utils import WSGIApplication

#: Version for the server
__version__ = "0.1"

class AlgoServer:
    """
    The main `:class:` for the WSGI Server.

    Parameters:
        host (str): 
            The host where the server serve. Default value: ''
        
        port (int):
            The port where the server should listen to. Default Value: 3000
        
        application (WSGIApplication):
            The main application for the server
    """

    #: A socket type for the WSGI Server. Usually socket.SOCK_STREAM
    socket_type = socket.SOCK_STREAM


    #: Address Family for the socket object. Usually AF_INET or
    #: Address Family Internet
    address_family  = socket.AF_INET


    #: The request queue size for the server. Default value: 5
    request_queue_size = 5


    #: Inorder to allow reuse the address, Make sure to make the value True
    allow_reuse_address = True


    #: The default request version should be HTTP/1.1
    default_request_version = "HTTP/1.1"


    #: The version of the server.
    server_version = "AlgoServer/%s" % (__version__)


    def __init__(self, host: t.Optional[str] = "",
            port: t.Optional[int] = 3000, application: WSGIApplication = None):
        
        #: The host where the server should listen to.
        #: Default value: '' which means it should listen
        #: To any network interfaces.
        self.host = host

        #: The port where the server should listen to. Default Value: 3000
        self.port = port

        #: The main WSGI application. If None, return Exception
        if application == None:
            pass

        self.application = application
        
    
        