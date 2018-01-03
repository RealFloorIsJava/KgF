"""Part of KgF.

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

import ssl
from http.server import HTTPServer
from socketserver import ThreadingMixIn
from threading import Thread

from kgf import kconfig
from pages.leaf import Leafs
from pages.master import MasterController
from web.handler import ServerHandler


class Webserver(Thread):
    """The HTTP web server."""

    def __init__(self):
        """Constructor."""
        super().__init__()
        # The internal http server which runs in the background
        self._httpd = None
        # The port the server runs on
        self._port = kconfig().get("port", 8091)
        # The certificate used for SSL (if enabled)
        self._certificate = kconfig().get("certificate", "cert.pem")
        # The private key for above certificate
        self._private_key = kconfig().get("privatekey", "priv.pem")
        # Whether SSL shall be used for connections
        self._use_ssl = kconfig().get("use_ssl", True)

        # Set up the controller for routing
        m = MasterController()

        # Add all leafs to the controller
        Leafs.add_leafs(m)

        # Set the master for the server handler
        ServerHandler.set_master(m)

    def run(self):
        """Starts the HTTP server in the background."""
        # Initialize the server
        socket_pair = ('', self._port)
        self._httpd = MultithreadedHTTPServer(socket_pair, ServerHandler)

        # Setup SSL if requested
        if self._use_ssl:
            tls = self._create_ssl_context()
            self._httpd.socket = tls.wrap_socket(self._httpd.socket,
                                                 server_side=True)

        # Let the HTTP server run in the background serving requests
        self._httpd.serve_forever()

    def stop(self):
        """Stops the HTTP server if it is running."""
        if self._httpd is not None:
            self._httpd.shutdown()

    def _create_ssl_context(self):
        """Creates a SSL context for HTTPS."""
        tls = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        tls.load_cert_chain(certfile=self._certificate,
                            keyfile=self._private_key)
        tls.set_ciphers(
            "HIGH:!aNULL:!eNULL:!EXPORT:!CAMELLIA:!DES:!MD5:!PSK:!RC4")
        return tls


class MultithreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """A HTTP server which handles each request in a seperate thread."""
    pass
