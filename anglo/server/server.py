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
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
import urllib.parse
import time
import sys
import io
import datetime
import typing as t
from anglo.utils import WSGIApplication
from anglo.utils import weekdays
from anglo.utils import months
from anglo.utils import to_bytes
from wsgiref.handlers import SimpleHandler
from platform import python_implementation



#: Version for the server
__version__ = "0.1"
sys_version = f"{python_implementation()}/{sys.version.split()[0]}"


class ServerHandler(SimpleHandler):
    """
    A server handler for handling requst from WSGI Environment.

    """
    server_software = f"AngloServer/{__version__} {sys_version}"

    def close(self):
        try:
            self.request_handler.log_request(
                self.status.split(' ',1)[0], self.bytes_sent
            )

        finally:
            SimpleHandler.close(self)


class AngloRequestHandler(BaseHTTPRequestHandler):
    """
    A Base class for handling Request.

    """
    __recv_value = 65537
    server_version = f"AngloServer/{__version__}"


    @property
    def stderr(self):
        return sys.stderr


    def get_environ(self):
        """
        Get the environment variables from WSGI Server. Learn more: https://www.python.org/dev/peps/pep-0333/#environ-variables
        """
        
        env = self.server.base_environ.copy()
        env['SERVER_PROTOCOL'] = self.request_version
        env['SERVER_SOFTWARE'] = self.server_version
        env['REQUEST_METHOD'] = self.command
        
        if '?' in self.path:
            path,query = self.path.split('?',1)
        else:
            path,query = self.path,''

        env['PATH_INFO'] = urllib.parse.unquote(path, 'iso-8859-1')
        env['QUERY_STRING'] = query

        host = self.address_string()
        if host != self.client_address[0]:
            env['REMOTE_HOST'] = host
        
        env['REMOTE_ADDR'] = self.client_address[0]

        if self.headers.get('content-type') is None:
            env['CONTENT_TYPE'] = self.headers.get_content_type()
        
        else:
            env['CONTENT_TYPE'] = self.headers['content-type']

        length = self.headers.get('content-length')
        if length:
            env['CONTENT_LENGTH'] = length

        for k, v in self.headers.items():

            k = k.replace('-','_').upper(); v=v.strip()
            if k in env:
                continue    # skip content length, type,etc.
            
            if 'HTTP_'+k in env:
                env['HTTP_' + k] += ',' + v # comma-separate multiple headers
            
            else:
                env['HTTP_' + k ] = v
        
        return env


    def handle(self):
        """
        Handle only single request.
        """

        self.raw_requestline = self.rfile.readline(self.__recv_value)

        if len(self.raw_requestline) > self.__recv_value - 1:

            self.requestline = ''
            self.request_version = ''
            self.command = ''
            self.send_error(414)

            return

        if not self.parse_request(): # An error code has been sent, just exit
            return

        handler = ServerHandler(
            self.rfile, self.wfile, self.stderr, self.get_environ(),
            multithread=False,
        )

        handler.request_handler = self      # backpointer for logging
        handler.run(self.server.application)


class AngloServerHandler(HTTPServer):
    """
    The main `:class:` for handling the Server.

    Parameters:
        This BaseClass doesnt required a parameter to be specify when initialized.

    When calling the class, you need to specify some parameters:
        host (str): 
            The host where the server should listen to
        
        port (int):
            The port where the server should listen to

        
    """

    __application = None

    @property
    def application(self):
        return self.__application

    @application.setter
    def application(self, app: WSGIApplication = None):
        if app == None:
            raise ValueError("Application cannot be None.")

        self.__application = app
        return self.__application


    def server_bind(self):
        """
        Bind the server to the host specified.
        """

        HTTPServer.server_bind(self)
        self.setup_environ()

    
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



class AngloServer:
    """
    The main `:class:` for the WSGI Server. Probably a HTTPServer
    with WSGI Protocol implemention. This server should use for development
    rather than production, haven't tried on production yet.

    Parameters:
        host (str):
            The host where the server should listen to.
        
        port (int):
            The port where the server should listen to.

        application (WSGIApplication):
            The main applicaation for WSGIEnvironment.

        debug (bool):
            Define if the debugger is True.
    """

    def __init__(self, host: t.Optional[str] = "localhost",
                port: t.Optional[int] = 3000, application: WSGIApplication = None,
                handler = AngloRequestHandler):

        self.server = AngloServerHandler((host, port), handler)
        self.server.application = application

    def run(self, debug: t.Optional[bool] = True):
        if debug:
            # Development | Debugging status
            self.server.serve_forever()

        else:
            self.server.serve_forever()


class AngloSocketServer:
    """
    The main `:class:` for the WSGI Socket Server.

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
    server_version = "AngloServer/%s" % (__version__)


    #: The base environment variables for the server.
    base_environ = {}

    def __init__(self, host: t.Optional[str] = "",
            port: t.Optional[int] = 3000, application: WSGIApplication = None):
        
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

        #: Setup environment variables for the WSGI Server.
        self.setup_environ()
        self.headers_set = []


    @property
    def version_string(self):
        return self.server_version


    def date_time_string(self, timestamp=None):
        """
        Convert datetime to string
        """

        if timestamp is None:
            timestamp = time.time()

        year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
        s = '%s, %02d %3s %4d %02d:%02d:%02d GMT' % (
            weekdays[wd],
            day, months[month], year,
            hh, mm, ss
        )
        return s

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
        
        env = self.base_environ
        env['SERVER_NAME'] = self.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PORT'] = str(self.port)
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
        print('(AngloServer) [%s] "%s %s %s"' % (
            datetime.datetime.now(), env["REQUEST_METHOD"],
            env["PATH_INFO"], env["SERVER_PROTOCOL"]
        ))

        result = self.application(env, self.start_response)

        #: Send the response from the client.
        self.finish_response(result)

    def parse_request(self, raw_request):

        # GET /foo?a=1&b=2 HTTP/1.1

        first_line = raw_request.split(b'\r\n', 1)[0].strip().decode()
        self.request_method, self.path, self.request_version = first_line.split()
        
        return (self.request_method, self.path, self.request_version)

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

    def get_environ(self):
        """
        Get the environment variables from WSGI Server. Learn more: https://www.python.org/dev/peps/pep-0333/#environ-variables
        """
        
        env = self.base_environ.copy()
        env['REQUEST_METHOD'] = self.request_method

        if '?' in self.path:
            path, query = self.path.split('?', 1)
        else:
            path, query = self.path, ''

        #: The path info of the server.
        #: Example: www.example.com/path - Where as path is the PATH_INFO
        env['PATH_INFO'] = urllib.parse.unquote(path)

        #: The query string of the server.
        #: Example: www.example.com/?search=test&encoding=utf-8 - Where as ? is the start of QUERY_STRING
        env['QUERY_STRING'] = query

        env['CONTENT_TYPE'] = self.headers.get('Content-Type', '')
        env['CONTENT_LENGTH'] = self.headers.get('Content-Length', '0')

        env['SERVER_PROTOCOL'] = self.request_version
        env['REMOTE_ADDR'] = self.client_address[0]
        env['REMOTE_PORT'] = self.client_address[1]

        env['wsgi.version'] = (1, 0)
        env['wsgi.url_scheme'] = 'http'
        env['wsgi.input'] = io.BytesIO(self.raw_req)
        env['wsgi.errors'] = sys.stderr
        env['wsgi.multithread'] = False
        env['wsgi.multiprocess'] = True
        env['wsgi.run_once'] = False

        for k, v in self.headers.items():
            k = k.replace('-', '_').upper()
            if k in env:
                continue
            env['HTTP_' + k] = v

        return env

    def start_response(self, status, headers, exc_info=None):
        """
        Start the response. Usually you can see this as a passed argument from the WSGI Application.
        """

        server_headers = [
            ('Date', self.date_time_string()),
            ('Server', self.version_string),
        ]

        headers = list(headers) + server_headers

        if exc_info:
            try:
                if self.headers_set:
                    # Re-raise original exception if headers sent
                    raise (exc_info[0], exc_info[1], exc_info[2])
            finally:
                exc_info = None     # avoid dangling circular ref

        self.headers_set[:] = [status, headers]

    def finish_response(self, body):
        """
        Finish the response and send it to the client.
        
        """
        try:
            status, headers = self.headers_set

            # status line
            response = (
                to_bytes(self.default_request_version) +
                b' ' +
                to_bytes(status) +
                b'\r\n'
            )
            # headers
            response += b'\r\n'.join([to_bytes(': '.join(x)) for x in headers])
            response += b'\r\n\r\n'

            # body
            for d in body:
                response += d

            self.client_connection.sendall(response)

        finally:
            self.client_connection.close()
