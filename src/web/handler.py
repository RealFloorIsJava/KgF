"""
    Part of KgF.

    Author: LordKorea
"""

from http.server import BaseHTTPRequestHandler
from kgf import print
from http.cookies import SimpleCookie
from web.session import Session
from cgi import FieldStorage, MiniFieldStorage
from urllib.parse import parse_qs
from traceback import extract_tb
from io import BytesIO


# noinspection PyPep8Naming
class ServerHandler(BaseHTTPRequestHandler):
    """ Takes incoming requests and handles them. """

    _master = None

    @staticmethod
    def set_master(mctrl):
        ServerHandler._master = mctrl

    def log_message(self, format, *args):
        pass  # No access log

    def do_request(self, params):
        # Setup results
        head = {}

        # Get the session (or create a new one)
        cookie = ""
        for key in self.headers:
            if key == "Cookie":
                cookie = self.headers[key]
        sc = SimpleCookie(cookie)
        if "session" in sc:
            sid = sc["session"].value
        else:
            sid = None
        session = Session.get_session(self.client_address[0], sid)
        if session[1]:  # was the session just created?
            cookie = "session=%s;Path=/;HttpOnly" % session[0].get_id()
            head["Set-Cookie"] = cookie
        session = session[0]
        session.refresh()

        # Get path and leaf
        path = self._get_path()
        leaf = path[0]
        path = path[1:]

        # Add the leaf parameter to the params
        ServerHandler._master.decorate_params(leaf, params)

        # Call the leaf/endpoint
        try:
            x = ServerHandler._master.call_endpoint(
                session.get_data(),
                path,
                params,
                self.headers
            )
        except Exception as e:
            # Endpoint call failed. Log the error
            print("=====[ERROR REPORT]=====")
            for entry in extract_tb(e.__traceback__):
                entry = (entry[0], entry[1], entry[2], entry[3])
                print("\tFile \"%s\", line %i, in %s\n\t\t%s" % entry)
            print(str(e))
            print("========================")
            self._reply(
                500,
                {"Content-Type": "text/plain"},
                ("The server encountered an unexpected condition and is unable"
                 " to continue.").encode()
            )
            return
        finally:
            for elem in params:
                try:
                    if elem.filename:
                        elem.file.close()
                except:
                    pass

        # Update request results
        code = x[0]
        head.update(x[1])
        response = x[2]
        if isinstance(response, str):
            response = response.encode()

        # Send the reply
        self._reply(code, head, response)

    def do_GET(self):
        """ Process a HTTP GET request. """
        self.do_request({})

    def do_POST(self):
        """ Process a HTTP POST request. """
        try:
            self.do_request(self._get_post_params())
        except RequestError as e:
            if e.length:
                self._abort(411, "Content-Length required")
            else:
                self._abort(400, "Media type not supplied")

    def handle_expect_100(self):
        """ No continuation requests """
        self._reply(417, {}, b"\0")  # 417 Expectation Failed
        return False

    def _get_path(self):
        """
            Get the path of this request
            Example:
                http://example.com/test/foo/bar.html?1=2
                ->
                ['test', 'foo', 'bar.hmtl']
        """
        raw = self.path

        # Remove trailing query string
        if "?" in raw:
            raw = raw[:raw.find("?")]

        path = []
        raw = raw.split("/")

        # Get path elements
        for element in raw:
            element = element.strip()
            if element == "":
                continue
            path.append(element)

        # If no path is present, supply default path
        if len(path) < 1:
            path = ["index"]

        return path

    def _get_post_params(self):
        """ Get post parameters """
        if "content-length" not in self.headers:
            raise RequestError(True)
        if "content-type" not in self.headers:
            print("Error: No content type for request!")
            raise RequestError(False)

        # Get parameter metadata
        type = self.headers["content-type"]
        length = int(self.headers["content-length"])
        type, args = self._parse_type(type)
        data = self.rfile.read(length)

        # Parse data
        if (type == "application/x-www-form-urlencoded" or
                    type == "text/plain"):
            d = parse_qs(data.decode(), keep_blank_values=True)

            # Keep lists only for array arguments
            for key in d:
                key = key
                if not key.endswith("[]"):
                    d[key] = d[key][0]
            return d
        elif type == "application/json":
            return {
                "data": data.decode()
            }
        elif type == "multipart/form-data" and "boundary" in args:
            fs = FieldStorage(
                BytesIO(data),
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'},
                keep_blank_values=True,
            )
            d = {}
            for key in fs:
                x = fs[key]
                if not x.filename:
                    if isinstance(x, (FieldStorage, MiniFieldStorage)):
                        d[x.name] = x.value
                    elif isinstance(x, list):
                        if x.name.endswith("[]"):
                            d[x.name] = x
                        elif len(x) > 0:
                            d[x.name] = x[0]
                else:
                    d[x.name] = x
            return d
        else:
            print("Currently unsupported %r %r %r" % (type, args, length))
            raise RequestError(False)

    def _parse_type(self, type):
        """ Parses the content type according to RFC 2045 """
        type = type.strip()
        if ";" not in type:
            return type, {}
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

    def _abort(self, code, msg):
        """ Report an error back to the client """
        self._reply(code, {"Content-Type": "text/plain"}, msg.encode())

    def _reply(self, code, headers, data):
        """ Send a HTTP response """
        self.server_version = "KgF/2.0"
        self.sys_version = "TeaPot/1.33.7"
        try:
            # Send HTTP status code
            self.send_response(code)

            # Send headers
            for key in headers:
                self.send_header(key, headers[key])
            self.end_headers()

            # Send reply (Ensure reply is never empty)
            if len(data) == 0:
                data = b"\0"
            self.wfile.write(data)
        except BrokenPipeError:
            pass  # Happen from time to time. Bad client.


class RequestError(Exception):
    """ Raised if either content type or content length is missing """

    def __init__(self, length):
        self.length = length
