"""
Part of KgF.

Author: LordKorea
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
    """ The HTTP web server """

    def __init__(self):
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

    def run(self):
        # Set up the controller for routing
        m = MasterController()

        # Add all leafs to the controller
        Leafs.add_leafs(m)

        # Set the master for the server handler
        ServerHandler.set_master(m)

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
        """ Stops the HTTP server """
        if self._httpd is not None:
            self._httpd.shutdown()

    def _create_ssl_context(self):
        """ Creates the SSL context, if required """
        tls = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        tls.load_cert_chain(
            certfile=self._certificate,
            keyfile=self._private_key
        )
        tls.set_ciphers(
            "HIGH:!aNULL:!eNULL:!EXPORT:!CAMELLIA:!DES:!MD5:!PSK:!RC4"
        )
        return tls


class MultithreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """ Multithreaded HTTP server """
    pass
