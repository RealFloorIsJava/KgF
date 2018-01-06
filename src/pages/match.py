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

from typing import Any, Dict, List, Tuple, cast

from model.match import Match
from model.participant import Participant
from nussschale.nussschale import nconfig
from nussschale.leafs.controller import Controller
from nussschale.session import SessionData
from nussschale.util.template import Parser
from nussschale.util.types import HTTPResponse, POSTParam


class MatchController(Controller):
    """Handles the /match leaf."""

    def __init__(self):
        """Constructor."""
        super().__init__()

        # Whether the logout link will be shown
        self._logout_shown = nconfig().get("login-required", True)

        # Only allow logged-in users in a match
        self.add_access_restriction(self.check_access)
        self.set_permission_fail_handler(self.fail_permission)

        # Match creation endpoint
        self.add_endpoint(self.create_match,
                          path_restrict={"create"},
                          params_restrict={"deckupload"})
        self.add_endpoint(self.fail_permission, path_restrict={"create"})

        # Match leaving
        self.add_endpoint(self.abandon_match, path_restrict={"abandon"})

        self.add_endpoint(self.match)

    def check_access(self,
                     session: SessionData,
                     path: List[str],
                     params: Dict[str, POSTParam],
                     headers: Dict[str, str]
                     ) -> bool:
        """Checks whether the user is logged in (and in a match).

        Args:
            session: The session data of the client.
            path: The path of the request.
            params: The HTTP POST parameters.
            headers: The HTTP headers that were sent by the client.

        Returns:
            True if the user is logged in and in a match (if required).
        """
        if "login" not in session:
            return False

        # Exceptions to the 'user has to be in a match rule':
        #  - Creating a match
        is_exempt = ("create" in path)
        if not is_exempt and Match.get_match_of_player(session["id"]) is None:
            return False

        return True

    def fail_permission(self,
                        session: SessionData,
                        path: List[str],
                        params: Dict[str, POSTParam],
                        headers: Dict[str, str]
                        ) -> Tuple[int, Dict[str, str], HTTPResponse]:
        """Handles unauthorized clients.

        Redirects the client to the dashboard.

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
                {"Location": "/dashboard"},
                "")

    def abandon_match(self,
                      session: SessionData,
                      path: List[str],
                      params: Dict[str, POSTParam],
                      headers: Dict[str, str]
                      ) -> Tuple[int, Dict[str, str], HTTPResponse]:
        """Handles the request to abandon a match.

        Redirects the client to the dashboard.

        Args:
            session: The session data of the client.
            path: The path of the request.
            params: The HTTP POST parameters.
            headers: The HTTP headers that were sent by the client.

        Returns:
            Returns 1) the HTTP status code 2) the HTTP headers to be
            sent and 3) the response to be sent to the client.
        """
        # Leave the match
        match = Match.get_match_of_player(session["id"])
        match.abandon_participant(session["id"])

        return (303,  # 303 See Other
                {"Location": "/dashboard"},
                "")

    def create_match(self,
                     session: SessionData,
                     path: List[str],
                     params: Dict[str, POSTParam],
                     headers: Dict[str, str]
                     ) -> Tuple[int, Dict[str, str], HTTPResponse]:
        """Handles the request to create a match.

        Redirects either to the match view (on success) or to the dashboard
        (when the deck is too big or another error occurs).

        Args:
            session: The session data of the client.
            path: The path of the request.
            params: The HTTP POST parameters.
            headers: The HTTP headers that were sent by the client.

        Returns:
            Returns 1) the HTTP status code 2) the HTTP headers to be
            sent and 3) the response to be sent to the client.
        """
        if Match.get_match_of_player(session["id"]) is not None:
            # The user already is in a match
            return (303,  # 303 See Other
                    {"Location": "/match"},
                    "")

        deckupload = cast(Any, params["deckupload"])
        if not deckupload.filename:
            # Make sure the uploaded thing is a file
            return self.fail_permission(session, path, params, headers)

        # Check the size of the upload
        fp = deckupload.file
        fp.seek(0, 2)
        size = fp.tell()
        fp.seek(0)
        if size > 800 * 1000:
            return (303,  # 303 See Other
                    {"Location": "/dashboard/deck_too_big"},
                    "")

        # Create a new match
        match = Match()

        # Create the deck from the upload
        try:
            data = fp.read().decode()
        except UnicodeDecodeError:
            return (415,  # 415 Unsupported Media Type
                    {"Content-Type": "text/plain"},
                    "Unsupported content type")
        success, msg = match.create_deck(data)

        # Check for failure
        if not success:
            return (303,  # 303 See Other
                    {"Location": "/dashboard/%s" % msg},
                    "")

        # Add the participant to the match
        part = Participant(session["id"], session["nickname"])
        match.add_participant(part)

        # Make the match available for others
        match.put_in_pool()

        return (303,  # 303 See Other
                {"Location": "/match"},
                "")

    def match(self,
              session: SessionData,
              path: List[str],
              params: Dict[str, POSTParam],
              headers: Dict[str, str]
              ) -> Tuple[int, Dict[str, str], HTTPResponse]:
        """Handles a request of the match view.

        Serves the match template.

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
        symtab = {"theme": session["theme"],
                  "showLogout": "" if self._logout_shown else None}

        # Parse the template
        data = Parser.get_template("./res/tpl/match.html", symtab)
        return (200,  # 200 OK
                {"Content-Type": "text/html; charset=utf-8"},
                data)
