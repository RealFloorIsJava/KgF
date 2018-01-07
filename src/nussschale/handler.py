"""Part of Nussschale.

MIT License
Copyright (c) 2017-2018 LordKorea

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import cgi
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from sys import exit
from traceback import extract_tb
from typing import Dict, List, Tuple, no_type_check
from urllib.parse import parse_qs

from nussschale.leafs.endpoint import _POSTParam
from nussschale.leafs.master import MasterController
from nussschale.nussschale import nlog
from nussschale.session import Session
from nussschale.util.heartbeat import Heartbeat


# Set the maximum request length, in bytes: 8 MiB
cgi.maxlen = 8 * 1024 * 1024  # type: ignore


class ServerHandler(BaseHTTPRequestHandler):
    """Handles incoming requests to the web server.

    Class Attributes:
        stop_connections: Whether to stop connections due to shutdown.
    """

    # Set some metrics
    server_version = "Nussschale/2.0"
    sys_version = "Python"
    protocol_version = "HTTP/1.1"

    # Set the default timeout
    timeout = 10

    # Whether to stop connections due to a shutdown
    stop_connections = False

    # The master controller which dispatches requests to leaves
    _master = None

    @staticmethod
    def set_master(mctrl: MasterController):
        """Sets the master controller for all handlers.

        Args:
            mctrl (obj): The master controller (pages.master) which receives
                the endpoint calls.
        """
        ServerHandler._master = mctrl

    def log_message(self, format: str, *args):
        """Overridden access log handler.

        This is automatically called, but we do not want to generate an access
        log so this method does nothing.

        Args:
            format: This parameter is ignored.
            *args: Additional positional arguments are ignored.
        """
        pass  # No logging is wanted!

    @no_type_check
    def do_request(self, params: Dict[str, _POSTParam]):
        """Performs the necessary actions to serve an HTTP request.

        Handles GET and POST requests in the same way.

        Args:
            params: The parameters that were supplied by the client.
                This includes POST parameters and file uploads.
        """
        if ServerHandler.stop_connections:
            self._abort(503, "Unavailable")  # 503 Service Unavailable
            self.close_connection = True
            return

        # Handle all heartbeats
        for fun in Heartbeat.heartbeats:
            try:
                fun()
            except Exception as e:
                nlog().log("An error occurred while executing"
                           " a request heartbeat.")
                for entry in extract_tb(e.__traceback__):
                    entry = tuple(entry[:4])
                    nlog().log("\tFile \"%s\", line %i, in %s\n\t\t%s" % entry)
                nlog().log(str(e))

                # Typically, faulty request heartbeats are a reason
                # to havoc... -- at least to save some log space!
                nlog().log("Heartbeat crash!")
                print("Heartbeat crash: See log for info.")
                exit(1)

        # Setup header dictionary
        head = {}

        # Find the session cookie (if any)
        cookie_hdr = ""
        for key in self.headers:
            if key == "Cookie":
                cookie_hdr = self.headers[key]
        cookie = SimpleCookie(cookie_hdr)

        # Extract the session ID
        if "session" in cookie:
            sid = cookie["session"].value
        else:
            sid = None

        # Fetch (or create) the session
        session = Session.get_session(self.client_address[0], sid)
        if session[1]:
            # The session is newly created, set the session ID cookie
            cookie = "session=%s;Path=/;HttpOnly" % session[0].sid
            head["Set-Cookie"] = cookie
        session = session[0]

        # Refresh the session timer to keep the user logged in
        session.refresh()

        # Get path and leaf, the leaf is the first value in the path,
        # see _get_path for more info
        path = self._get_path()
        leaf = path[0]
        path = path[1:]

        # Add the magic leaf parameter to the params
        MasterController.decorate_params(leaf, params)

        # Call the leaf/endpoint
        x = None
        try:
            x = ServerHandler._master.call_endpoint(session.data,
                                                    path,
                                                    params,
                                                    self.headers)
        except Exception as e:
            # Endpoint call failed. Log the error
            nlog().log("=====[ERROR REPORT]=====")

            # Walk through the backtrace
            for entry in extract_tb(e.__traceback__):
                entry = tuple(entry[:4])
                nlog().log("\tFile \"%s\", line %i, in %s\n\t\t%s" % entry)

            # Log the string representation of the exception as a summary
            nlog().log(str(e))
            nlog().log("========================")

            # Notify the user that the request failed
            self._reply(500,  # 500 Internal Server Error
                        {"Content-Type": "text/plain; charset=utf-8"},
                        ("The server encountered an unexpected condition and"
                         " is unable to continue.").encode())
            return
        finally:
            # For file uploads: Close all uploaded file handles that have been
            # opened
            for val in params.values():
                if hasattr(val, "filename"):
                    val.file.close()
        assert x is not None

        # Update request results
        code = x[0]
        head.update(x[1])
        response = x[2]

        # The response might not be properly encoded (it is not required to be
        # encoded). In this case we encode it here
        if isinstance(response, str):
            response = response.encode()

        # Send the reply to the client
        self._reply(code, head, response)

    def do_GET(self):  # noqa: N802
        """Processes an HTTP GET request."""
        # Handle a GET request as a POST request with no parameters
        self.do_request({})

    def do_POST(self):  # noqa: N802
        """Processes an HTTP POST request."""
        try:
            self.do_request(self._get_post_params())
        except RequestError as e:
            if e.length:
                # 411 Length Required
                self._abort(411, "Content-Length required")
            else:
                # 400 Bad Request
                self._abort(400, "Media type not supplied/supported")

    def handle_expect_100(self) -> bool:
        """Handles HTTP continuation requests.

        The web server rejects all continuation requests using the appropriate
        HTTP status code.

        Returns:
            Always False according to the documentation of http.server.
        """
        self._reply(417, {}, b"\0")  # 417 Expectation Failed
        return False

    def _get_path(self) -> List[str]:
        """Parses the path for this request.

        The path consists of all slash-seperated values after the domain in
        the request URI. The query string is not part of the path.
        The first element in the path is the 'leaf' which decides which page
        will handle the request.
        Example:
        http://example.com/test/foo/bar.html?x=2
        Path is ['test', 'foo', 'bar.html']
        The leaf is 'test'

        Returns:
            The path.
        """
        # Get the path from the web server
        raw_str = self.path

        # Remove trailing query string
        if "?" in raw_str:
            raw_str = raw_str[:raw_str.find("?")]

        # Split the raw path into the slash seperated parts
        path = []
        raw = raw_str.split("/")

        # Trim whitespace at beginning and end of each element and ignore empty
        # ones
        for element in raw:
            element = element.strip()
            if element == "":
                continue
            path.append(element)

        # If no path is present return default path
        if len(path) < 1:
            path = ["index"]

        return path

    @no_type_check
    def _get_post_params(self) -> Dict[str, _POSTParam]:
        """Retrieves the POST parameters. Also handles file uploads.

        Returns:
            The POST parameters. File uploads are returned as open file-like
            objects in the dictionary.

        Raises:
            RequestError: When length or content type is not supplied by the
                client.
        """
        if "content-length" not in self.headers:
            # This server requires a content length to be supplied
            raise RequestError(True)

        if "content-type" not in self.headers:
            # This server also requires a valid content type
            raise RequestError(False)

        # Get parameter metadata
        type = self.headers["content-type"]
        length = int(self.headers["content-length"])

        # Parse the content type and read the POST data
        type, args = self._parse_type(type)
        data = self.rfile.read(length)

        # Parse data
        if (type == "application/x-www-form-urlencoded"
                or type == "text/plain"):
            # The regular key=value&key2=value2... format
            d = parse_qs(data.decode(), keep_blank_values=True)

            # Keep lists only for array arguments.
            # According to the documentation of urllib, parse_qs might return
            # multiple values even for non-array arguments
            for key in d:
                if not key.endswith("[]"):
                    # Just use the first element, even if multiple are supplied
                    d[key] = d[key][0]
            return d
        elif type == "application/json":
            # POST data is JSON data
            return {"data": data.decode()}
        elif type == "multipart/form-data" and "boundary" in args:
            # POST data is a HTTP file upload
            try:
                fs = cgi.FieldStorage(BytesIO(data),
                                      headers=self.headers,
                                      environ={'REQUEST_METHOD': 'POST'},
                                      keep_blank_values=True)
            except ValueError:
                nlog().log("File upload was too big!")
                return {}
            d = {}
            for key in fs:
                x = fs[key]
                if not x.filename:
                    if isinstance(x, (cgi.FieldStorage, cgi.MiniFieldStorage)):
                        # MiniFieldStorage can result from an additional
                        # query string
                        d[x.name] = x.value
                    elif isinstance(x, list):
                        # Regular POST variable
                        if key.endswith("[]"):
                            # Array argument
                            d[key] = x
                        elif len(x) > 0:
                            # Non-array argument. However, empty non-array
                            # arguments are ignored
                            d[key] = x[0]
                else:
                    # In the case of the key having a file just use the
                    # result of the field storage parsing
                    fp = x.file
                    fp.seek(0, 2)
                    size = fp.tell()
                    fp.seek(0)
                    nlog().log("File upload: '%s', %i bytes" % (x.filename,
                                                                size))
                    d[x.name] = x
            return d
        else:
            # Unsupported content type!
            nlog().log("Currently unsupported %r %r %r" % (type, args, length))
            raise RequestError(False)

    @staticmethod
    def _parse_type(type: str) -> Tuple[str, Dict[str, str]]:
        """Parses the content type according to RFC 2045

        Args:
            type (str): The raw content type header.

        Returns:
            (str, dict): The first element returned is the actual content-type,
                the dictionary contains all arguments supplied for the type.
        """
        type = type.strip()
        if ";" not in type:
            # Regular content type without arguments
            return type, {}

        # Extract the arguments
        ls = type.split(";")
        type = ls[0]
        param = {}
        for elem in ls[1:]:
            elem = elem.strip()

            # Ignore malformed elements
            if "=" not in elem:
                continue
            kw = elem.split("=", 1)

            # Get rid of quotes
            if len(kw[1]) > 1:
                if kw[1][0] == "\"" and kw[1][-1] == "\"":
                    kw[1] = kw[1][1:-1]

            # Add the parameter
            param[kw[0]] = kw[1]

        return type, param

    def _abort(self, code: int, msg: str):
        """Reports an error back to the client.

        Args:
            code: The HTTP status code that will be sent.
            msg: The response string that will be sent.
        """
        self._reply(code,
                    {"Content-Type": "text/plain; charset=utf-8"},
                    msg.encode())

    def _reply(self, code: int, headers: Dict[str, str], data: bytes):
        """Sends an HTTP response to the client.

        Args:
            code: The HTTP status code that will be sent.
            headers: A dictionary containing headers that will be sent.
                Dictionary keys are header names and entries are header values.
            data: The response that will be sent to the client.
        """
        try:
            # Send HTTP status code
            self.send_response(code)

            # Send headers
            for key in headers:
                if key != "Content-Length":
                    self.send_header(key, headers[key])

            # Send content length header
            self.send_header("Content-Length", str(max(1, len(data))))

            self.end_headers()

            # Send reply
            # The reply may never be empty!
            if len(data) == 0:
                data = b"\0"
            self.wfile.write(data)
        except BrokenPipeError:
            pass  # These happen from time to time. Bad client.


class RequestError(Exception):
    """Raised if either content type or length is missing in the request."""

    def __init__(self, length: bool) -> None:
        """Constructor.

        Args:
            length: Whether the error was caused by the content length being
                not present.
        """
        self.length = length
