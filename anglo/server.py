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
from anglo.utils import weekdays
from anglo.utils import months

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


    #: The request queue size for the server to listen to. Default value: 5
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

        #: The socket object of the server.
        self.socket = socket.socket(self.address_family, self.socket_type)

        #: Bind the server to the address
        self.server_bind((self.host, self.port))
        
        #: Start the server by listening to request_queue_size
        self.server_listen()

    def server_bind(self, server_address: tuple):
        """
        Bind the server to the address given

        Arguments:
            server_address (tuple):
                The server address to be bind to. Must be a tuple (<host>, <port>)
        """

        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        #: Bind the socket to the address
        self.socket.bind(server_address)
        
        #: Set the server name by the socket host.
        host, port  = self.socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)


    def server_listen(self):
        #: Start the server by listening to request queue size.
        self.socket.listen(self.request_queue_size)
    

    def setup_environ(self):
        """
        Set the environment variables for the WSGI Server. See: https://www.python.org/dev/peps/pep-0333/#environ-variables 
        for more information.
        """

        #: Set up base environment
        
        env = self.base_environ = {}
        env['SERVER_NAME'] = self.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PORT'] = str(self.server_port)
        env['REMOTE_HOST'] = ''
        env['CONTENT_LENGTH'] = ''
        env['SCRIPT_NAME'] = ''

    def serve_forever(self):
        """
        Serve the server forever while the application is running.
        """

        while True:
            #: Handle the request
            self.handle_request()

            #: After the one request, close the connection between the client
            self.client_connection.close()
            
    
    def handle_request(self):
        """
        Handle the request for the WSGI Server. Only one request that can be handle
        at the same time
        """

        #: Get the connection, address for the upcoming connection.
        self.client_connection, self.client_address = self.socket.accept()
        
        #: The value for the bytes to receive. Max value is 65536
        recv_value = 65536

        #: Raw request from the client.
        self.raw_req = self.client_connection.recv(recv_value)

        #: Parse the raw request as well as the headers from it. 
        self.parse_request(self.raw_req)
        
        #: The headers from the parsed raw request
        headers = self.parse_headers(self.raw_req)
        
        #: The legnth of the headers from the parsed headers from raw request.
        length = int(self.headers.get('Content-Length', '0'))

        while len(self.raw_req) == length:
            # If the length of the raw request is equal to length of the header, add it to the raw req.
            self.raw_req += self.client_connection.recv(recv_value)


        #: Get the environment variable of the WSGI Server.
        env = self.get_environ()

        # Print the output of the request.
        print('(%s) [%s] "%s %s %s"' % (
            self.server_version, datetime.datetime.now(), env["REQUEST_METHOD"],
            env["PATH_INFO"], env["SERVER_PROTOCOL"]
        ))

    def parse_request(self, raw_request):

        # GET /foo?a=1&b=2 HTTP/1.1

        first_line = raw_request.split(b'\r\n', 1)[0].strip().decode()
        
        (self.request_method,   # GET
         self.path,             # /foo?a=1&b=2
         self.request_version   # HTTP/1.1
        ) = first_line.split()

    def parse_headers(self, raw_request):

        #: The header string from the raw_request
        header_string = raw_request.split(b'\r\n\r\n', 1)[0].decode()
        
        self.headers = headers = {}
        
        for header in header_string.splitlines()[1:]:
            k, v = header.split(':', 1)
            if headers.get(k):
                #: Multiple with the same name header
                headers[k] += ', ' + v.strip()

            else:
                headers[k] = v.strip()

