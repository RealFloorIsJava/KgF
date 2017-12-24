"""
    Part of KgF.

    Author: LordKorea
"""

import ssl
from http.server import HTTPServer
from threading import Thread
from socketserver import ThreadingMixIn
from kgf import kconfig
from web.handler import ServerHandler
from pages.master import MasterController
from pages.leaf import Leafs


class Webserver(Thread):
    """
        The HTTP web server
    """

    def __init__(self):
        super().__init__()
        self._httpd = None
        self._port = kconfig().get("port", 8091)
        self._certificate = kconfig().get("certificate", "cert.pem")
        self._private_key = kconfig().get("privatekey", "priv.pem")

    def run(self):
        m = MasterController()
        Leafs.add_leafs(m)
        ServerHandler.set_master(m)
        socket_pair = ('', self._port)
        self._httpd = MultithreadedHTTPServer(socket_pair, ServerHandler)
        if kconfig().get("useSSL", "yes") == "yes":
            tls = self._create_ssl_context()
            self._httpd.socket = tls.wrap_socket(
                self._httpd.socket,
                server_side=True
            )
        self._httpd.serve_forever()

    def stop(self):
        if self._httpd is not None:
            self._httpd.shutdown()

    def _create_ssl_context(self):
        # Server has it
        # noinspection PyUnresolvedReferences
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
