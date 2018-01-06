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

from typing import Dict, List, Tuple

from kgf import kconfig
from pages.controller import Controller
from pages.templates.engine import Parser
from util.types import HTTPResponse, POSTParam
from web.session import SessionData


class DeckeditController(Controller):
    """Handles the /deckedit leaf."""

    def __init__(self):
        """Constructor."""
        super().__init__()

        # Whether the logout link will be shown
        self._logout_shown = kconfig().get("login-required", True)

        # Only allow logged-in users
        self.add_access_restriction(self.check_access)
        self.set_permission_fail_handler(self.fail_permission)

        self.add_endpoint(self.deckedit)

    def check_access(self,
                     session: SessionData,
                     path: List[str],
                     params: Dict[str, POSTParam],
                     headers: Dict[str, str]
                     ) -> bool:
        """Checks whether the user is logged in.

        Args:
            session: The session data of the client.
            path: The path of the request.
            params: The HTTP POST parameters.
            headers: The HTTP headers that were sent by the client.

        Returns:
            True if and only if the user is logged in.
        """
        return "login" in session

    def fail_permission(self,
                        session: SessionData,
                        path: List[str],
                        params: Dict[str, POSTParam],
                        headers: Dict[str, str]
                        ) -> Tuple[int, Dict[str, str], HTTPResponse]:
        """Handles unauthorized clients.

        Redirects the client to the index page.

        Args:
            session: The session data of the client.
            path: The path of the request.
            params: The HTTP POST parameters.
            headers: The HTTP headers that were sent by the client.

        Returns:
            Returns 1) the HTTP status code 2) the HTTP headers to be
            sent and 3) the response to be sent to the client.
        """
        return (303,  # 303 See Other
                {"Location": "/index/authfail"},
                "")

    def deckedit(self,
                 session: SessionData,
                 path: List[str],
                 params: Dict[str, POSTParam],
                 headers: Dict[str, str]
                 ) -> Tuple[int, Dict[str, str], HTTPResponse]:
        """Handles requests for the deck editor page.

        Serves the deck editor template.

        Args:
            session: The session data of the client.
            path: The path of the request.
            params: The HTTP POST parameters.
            headers: The HTTP headers that were sent by the client.

        Returns:
            Returns 1) the HTTP status code 2) the HTTP headers to be
            sent and 3) the response to be sent to the client.
        """
        # Populate symbol table
        symtab = {"nickname": session["nickname"],
                  "theme": session["theme"],
                  "showLogout": "" if self._logout_shown else None}

        # Parse the template
        data = Parser.get_template("./res/tpl/deckedit.html", symtab)
        return (200,  # 200 OK
                {"Content-Type": "text/html; charset=utf-8"},
                data)
