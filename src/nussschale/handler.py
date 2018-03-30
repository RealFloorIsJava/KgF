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
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from urllib.parse import parse_qs

from nussschale.leafs.endpoint import _POSTParam
from nussschale.leafs.master import MasterController
from nussschale.nussschale import nlog
from nussschale.session import Session
from nussschale.util.fileupload import IOWrapper
from nussschale.util.heartbeat import Heartbeat
from nussschale.util.lcdict import LowerCaseDict


_RawPOSTParam = Union[List[Any], cgi.FieldStorage, cgi.MiniFieldStorage]


class ServerHandler(BaseHTTPRequestHandler):
    """Handles incoming requests to the web server.

    Class Attributes:
        stop_connections: Whether to stop connections due to shutdown.
        max_content_length: The maximum content length.
    """

    # Some attributes for changing the base class behavior
    server_version = "Nussschale/2.0"
    sys_version = "Python"
    protocol_version = "HTTP/1.1"
    timeout = 10  # Set the default timeout

    # Whether to stop connections due to a shutdown
    stop_connections = False

    # The maximum content length, 8MiB
    max_content_length = 8 * 1024 * 1024

    # The master controller which dispatches requests to leaves
    _master = None  # type: MasterController

    def __init__(self, *args, **kwargs) -> None:
        """Constructor.

        Args:
            *args: Forwarded to base constructor.
            **kwargs: Forwarded to base constructor.
        """
        # The stringified headers. All header names are lowercase!
        self._str_headers = LowerCaseDict()  # type: LowerCaseDict[str]

        # Called last because this handles the request!
        super().__init__(*args, **kwargs)

    @staticmethod
    def set_master(mctrl: MasterController) -> None:
        """Sets the master controller for all handlers.

        Args:
            mctrl (obj): The master controller (pages.master) which receives
                the endpoint calls.
        """
        ServerHandler._master = mctrl

    def log_message(self, format: str, *args) -> None:
        """Overridden access log handler.

        This is automatically called, but we do not want to generate an access
        log so this method does nothing.

        Args:
            format: This parameter is ignored.
            *args: Additional positional arguments are ignored.
        """
        pass  # No logging is wanted!

    @staticmethod
    def do_heartbeat() -> None:
        """Runs all heartbeat routines."""
        for fun in Heartbeat.heartbeats:
            try:
                fun()
            except Exception as e:
                nlog().log("An error occurred while executing"
                           " a request heartbeat.")
                for entry in extract_tb(e.__traceback__):
                    data = cast(Tuple[str, int, str, str],
                                tuple([entry[i] for i in range(4)]))
                    nlog().log("\tFile \"%s\", line %i, in %s\n\t\t%s" % data)
                nlog().log(str(e))

                # Typically, faulty request heartbeats are a reason
                # to havoc... -- at least to save some log space!
                nlog().log("Heartbeat crash!")
                print("Heartbeat crash: See log for info.")
                exit(1)

    def fetch_session(self) -> Tuple[Session, bool]:
        # Find the session cookie (if any) and extract the ID
        sid = None  # type: Optional[str]
        if "cookie" in self._str_headers:
            cookie = SimpleCookie(self._str_headers["cookie"])  # type: ignore
            if "session" in cookie:
                sid = cookie["session"].value
        if sid == "":
            nlog().log("Empty session ID, reassigning...")
            sid = None

        # Fetch (or create) the session
        session = Session.get_session(self.client_address[0], sid)

        # Refresh the session timer to keep the user logged in
        session[0].refresh()

        return session

    def convert_headers(self) -> None:
        """Loads the headers into the lower case header dictionary."""
        for key in self.headers.keys():
            assert isinstance(key, str), "header key is no str"
            val = self.headers[key]
            if not isinstance(val, str):
                nlog().log("Warning: %s header is no string" % key)
                continue
            self._str_headers[key.lower()] = val

    def do_request(self, params: Dict[str, _POSTParam]) -> None:
        """Performs the necessary actions to serve an HTTP request.

        Handles GET and POST requests in the same way.

        Args:
            params: The parameters that were supplied by the client.
                This includes POST parameters and file uploads.
        """
        if ServerHandler.stop_connections:
            self._abort(503, "Unavailable")  # 503 Service Unavailable
            self.close_connection = True  # noqa  # belongs to base class
            return

        # Handle all heartbeats
        ServerHandler.do_heartbeat()

        # Setup result header dictionary
        headers_out = {}

        # Fetch the session
        session_qry = self.fetch_session()
        if session_qry[1]:
            # The session is newly created, set the session ID cookie
            cookie = "session=%s;Path=/;HttpOnly" % session_qry[0].sid
            headers_out["set-cookie"] = cookie
        session = session_qry[0]

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
                                                    self._str_headers)
        except Exception as e:
            # Endpoint call failed. Log the error
            nlog().log_error(e, "endpoint call %s" % path)

            # Notify the user that the request failed
            self._abort(500,  # 500 Internal Server Error
                        "The server encountered an unexpected condition"
                        " and is unable to continue.")
            return
        finally:
            # For file uploads: Close all uploaded file handles that have been
            # opened
            for param in params.values():
                if isinstance(param, IOWrapper):
                    param.file.close()
        assert x is not None

        # Update request results
        code = x[0]
        headers_out.update(x[1])
        response = x[2]

        # The response might not be properly encoded (it is not required to be
        # encoded). In this case we encode it here.
        if isinstance(response, str):
            response = response.encode()

        # Send the reply to the client
        self._reply(code, headers_out, response)

    def do_GET(self) -> None:  # noqa: N802  # required by library
        """Processes an HTTP GET request."""
        # Handle a GET request as a POST request with no parameters
        self.convert_headers()
        self.do_request({})

    def do_POST(self) -> None:  # noqa: N802  # required by library
        """Processes an HTTP POST request."""
        self.convert_headers()
        try:
            self.do_request(self._get_post_params())
        except LengthMissingException:
            # 411 Length Required
            self._abort(411, "Content-Length required")
        except MediaTypeInvalidException:
            # 415 Unsupported Media Type
            self._abort(415, "Unsupported Media Type")

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

    def _unwrap_param(self, allow_list: bool, param: _RawPOSTParam
                      ) -> _POSTParam:
        """Unwraps a raw parameter.

        Args:
            allow_list: Whether lists of parameters are allowed.
            param: The parameter, as received from the FieldStorage.

        Returns:
            An unwrapped POST parameter.

        Raises:
            ValueError: For unsupported parameter types.
        """
        if isinstance(param, list):
            if allow_list:
                res = []  # type: List[Union[str, IOWrapper]]
                for x in param:
                    val = self._unwrap_param(False, x)
                    assert not isinstance(val, list)
                    res.append(val)
                return res
            else:
                return self._unwrap_param(False, param[0])
        elif isinstance(param, cgi.MiniFieldStorage):
            return param.value
        elif isinstance(param, cgi.FieldStorage):
            if param.file is None:
                assert isinstance(param.value, str)
                return param.value
            else:
                if param.filename == None:
                    return param.value
                else :
                    fp = param.file
                    fp.seek(0, 2)
                    size = fp.tell()
                    fp.seek(0)
                    nlog().log("File upload: '%s', %i bytes" % (param.filename,
                                                                size))
                    return IOWrapper(param.file, param)
        else:
            raise ValueError("Unsupported parameter type")

    def _get_post_params(self) -> Dict[str, _POSTParam]:
        """Retrieves the POST parameters. Also handles file uploads.

        Returns:
            The POST parameters. Consist of strings, lists and IO wrappers.

        Raises:
            RequestError: When length or content type is not supplied by the
                client.
        """
        if "content-length" not in self._str_headers:
            # This server requires a content length to be supplied
            raise LengthMissingException()

        if "content-type" not in self._str_headers:
            # This server also requires a valid content type
            raise MediaTypeInvalidException()

        # Get parameter metadata
        content_type = self._str_headers["Content-Type"]
        content_length = int(self._str_headers["Content-Length"])
        if content_length > ServerHandler.max_content_length:
            nlog().log("Request was too big!")
            return {}

        # Parse the content type and read the POST data
        content_type, type_args = self._parse_type(content_type)
        raw_data = self.rfile.read(content_length)

        # Parse data
        result = {}  # type: Dict[str, _POSTParam]
        if (content_type == "application/x-www-form-urlencoded"
                or content_type == "text/plain"):
            # The regular key=value&key2=value2... format
            qs_data = parse_qs(raw_data.decode(), keep_blank_values=True)

            # Keep lists only for array arguments.
            # According to the documentation of urllib, parse_qs might return
            # multiple values even for non-array arguments
            for key in qs_data:
                if not key.endswith("[]"):
                    # Just use the first element, even if multiple are supplied
                    result[key] = qs_data[key][0]
                else:
                    result[key] = cast(List[Union[str, IOWrapper]],
                                       qs_data[key])
            return result
        elif content_type == "multipart/form-data" and "boundary" in type_args:
            # POST data is a HTTP file upload
            fs = cgi.FieldStorage(BytesIO(raw_data),
                                  headers=self._str_headers,
                                  environ={'REQUEST_METHOD': 'POST'},
                                  keep_blank_values=True)
            for key in fs.keys():
                raw_val = fs[key]
                val = self._unwrap_param(True, raw_val)
                result[key] = val
            return result
        else:
            nlog().log("Currently unsupported type '%r' (with args '%r'),"
                       " %r bytes" % (content_type, type_args, content_length))
            raise MediaTypeInvalidException()

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

    def _abort(self, code: int, msg: str) -> None:
        """Reports an error back to the client.

        Args:
            code: The HTTP status code that will be sent.
            msg: The response string that will be sent.
        """
        self._reply(code,
                    {"content-type": "text/plain; charset=utf-8"},
                    msg.encode())

    def _reply(self, code: int, headers: Dict[str, str], data: bytes) -> None:
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
                if key != "content-length":
                    self.send_header(key, headers[key])

            # Send content length header
            self.send_header("content-length", str(max(1, len(data))))

            self.end_headers()

            # Send reply
            # The reply may never be empty!
            if len(data) == 0:
                data = b"\0"
            self.wfile.write(data)
        except BrokenPipeError:
            pass  # These happen from time to time. Bad client.


class MediaTypeInvalidException(Exception):
    """Raised when the media type is either missing or invalid."""
    pass


class LengthMissingException(Exception):
    """Raised when the content length is missing."""
    pass
