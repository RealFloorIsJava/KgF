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

from random import randint
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from nussschale.leafs.controller import Controller
from nussschale.nussschale import nconfig
from nussschale.session import SessionData
from nussschale.util.template import Parser
from nussschale.util.types import HTTPResponse, POSTParam


class IndexController(Controller):
    """Handles the /index leaf."""

    def __init__(self):
        """Constructor."""
        super().__init__()

        # Load the login password
        self._login_pw = nconfig().get("site-pw", "loremipsum")

        # Whether a login is required
        self._login_required = nconfig().get("login-required", True)

        # Adds the catch-all endpoint if login is not required
        if not self._login_required:
            self.add_endpoint(self.catchall)

        self.add_endpoint(self.login, params_restrict={"pw"})
        self.add_endpoint(self.logout, path_restrict={"logout"})
        self.add_endpoint(self.index)

    def catchall(self,
                 session: SessionData,
                 path: List[str],
                 params: Dict[str, POSTParam],
                 headers: Dict[str, str]
                 ) -> Tuple[int, Dict[str, str], HTTPResponse]:
        """Handles creating a user when login is disabled.

        Will redirect to the dashboard.

        Args:
            session: The session data of the client.
            path: The path of the request.
            params: The HTTP POST parameters.
            headers: The HTTP headers that were sent by the client.

        Returns:
            Returns 1) the HTTP status code 2) the HTTP headers to be
            sent and 3) the response to be sent to the client.
        """
        if "login" not in session:
            self._create_user(session)
        return (303,  # 303 See Other
                {"Location": "/dashboard"},
                "")

    def login(self,
              session: SessionData,
              path: List[str],
              params: Dict[str, POSTParam],
              headers: Dict[str, str]
              ) -> Optional[Tuple[int, Dict[str, str], HTTPResponse]]:
        """Handles requests made with the login form.

        Will redirect (via the index endpoint) to the dashboard on success.
        If the login fails the client is redirected to the index endpoint.

        Args:
            session: The session data of the client.
            path: The path of the request.
            params: The HTTP POST parameters.
            headers: The HTTP headers that were sent by the client.

        Returns:
            Returns 1) the HTTP status code 2) the HTTP headers to be
            sent and 3) the response to be sent to the client.
        """
        if params["pw"] == self._login_pw:
            self._create_user(session)
            return (303,  # 303 See Other
                    {"Location": "/dashboard"},
                    "")
        return (303,  # 303 See Other
                {"Location": "/index/pwfail"},
                "")

    @staticmethod
    def _create_user(session: SessionData):
        """Initializes a temporary user account.

        Args:
            session: The session data the user will be created in.
        """
        session["login"] = True
        session["id"] = str(uuid4())
        session["nickname"] = "Meme" + str(randint(10000, 99999))
        session["theme"] = "light"

    def logout(self,
               session: SessionData,
               path: List[str],
               params: Dict[str, POSTParam],
               headers: Dict[str, str]
               ) -> Tuple[int, Dict[str, str], HTTPResponse]:
        """Handles logout requests.

        Will show the index page (via the index endpoint).

        Args:
            session: The session data of the client.
            path: The path of the request.
            params: The HTTP POST parameters.
            headers: The HTTP headers that were sent by the client.

        Returns:
            Returns 1) the HTTP status code 2) the HTTP headers to be
            sent and 3) the response to be sent to the client.
        """
        if "login" in session:
            session.remove("login")

        return self.index(session, path, params, headers)

    def index(self,
              session: SessionData,
              path: List[str],
              params: Dict[str, POSTParam],
              headers: Dict[str, str]
              ) -> Tuple[int, Dict[str, str], HTTPResponse]:
        """Handles requests for the index page.

        Redirects to the dashboard if the client is logged in. Serves the
        start template otherwise.

        Args:
            session: The session data of the client.
            path: The path of the request.
            params: The HTTP POST parameters.
            headers: The HTTP headers that were sent by the client.

        Returns:
            Returns 1) the HTTP status code 2) the HTTP headers to be
            sent and 3) the response to be sent to the client.
        """
        # If the user is already logged in, send him to the dashboard
        if "login" in session:
            return (303,  # 303 See Other
                    {"Location": "/dashboard"},
                    "")

        # Populate symbol table
        symtab = {}  # type: Any
        if "authfail" in path:
            symtab["authfail"] = ""
        elif "pwfail" in path:
            symtab["pwfail"] = ""
        elif "logout" in path:
            symtab["logout"] = ""

        # Parse the template
        data = Parser.get_template("./res/tpl/start.html", symtab)
        return (200,  # 200 OK
                {"Content-Type": "text/html; charset=utf-8"},
                data)
