"""Part of KgF.

MIT License
Copyright (c) 2017 LordKorea

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

from kgf import kconfig
from model.match import Match
from model.participant import Participant
from pages.controller import Controller
from pages.templates.engine import Parser


class MatchController(Controller):
    """Handles the /match leaf."""

    def __init__(self):
        """Constructor."""
        super().__init__()

        # Whether the logout link will be shown
        self._logout_shown = kconfig().get("login-required", True)

        # Only allow logged-in users in a match
        self.add_access_restriction(self.check_access)
        self.set_permission_fail_handler(self.fail_permission)

        # Match creation endpoint
        self.add_endpoint(self.create_match,
                          path_restrict={"create"},
                          params_restrict={"deckupload"})
        self.add_endpoint(self.fail_permission, path_restrict={"create"})

        # Match joining endpoint
        self.add_endpoint(self.join_match, path_restrict={"join"})

        # Match leaving
        self.add_endpoint(self.abandon_match, path_restrict={"abandon"})

        self.add_endpoint(self.match)

    def check_access(self, session, path, params, headers):
        """Checks whether the user is logged in (and in a match).

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            bool: True if the user is logged in and in a match (if required).
        """
        if "login" not in session:
            return False

        # Exceptions to the 'user has to be in a match rule':
        #  - Joining a match
        #  - Creating a match
        is_exempt = ("create" in path) or ("join" in path)
        if not is_exempt and Match.get_match_of_player(session["id"]) is None:
            return False

        return True

    def fail_permission(self, session, path, params, headers):
        """Handles unauthorized clients.

        Redirects the client to the dashboard.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        return (303,  # 303 See Other
                {"Location": "/dashboard"},
                "")

    def abandon_match(self, session, path, params, headers):
        """Handles the request to abandon a match.

        Redirects the client to the dashboard.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        # Leave the match
        match = Match.get_match_of_player(session["id"])
        match.abandon_participant(session["id"])

        return (303,  # 303 See Other
                {"Location": "/dashboard"},
                "")

    def join_match(self, session, path, params, headers):
        """Handles the request to join an existing match.

        Redirects the client to the match view.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        if Match.get_match_of_player(session["id"]) is not None:
            # The user is already in a match
            return (303,  # 303 See Other
                    {"Location": "/match"},
                    "")

        # Get the transmitted match ID
        try:
            id = int(path[-1])
        except ValueError:
            return self.fail_permission(session, path, params, headers)

        # Get the match from the pool
        match = Match.get_by_id(id)
        if match is None or match.has_started():
            return self.fail_permission(session, path, params, headers)

        # Put the player into the match
        part = Participant(session["id"], session["nickname"])
        match.add_participant(part)

        return (303,  # 303 See Other
                {"Location": "/match"},
                "")

    def create_match(self, session, path, params, headers):
        """Handles the request to create a match.

        Redirects either to the match view (on success) or to the dashboard
        (when the deck is too big).

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        if Match.get_match_of_player(session["id"]) is not None:
            # The user already is in a match
            return (303,  # 303 See Other
                    {"Location": "/match"},
                    "")

        if not params["deckupload"].filename:
            # Make sure the uploaded thing is a file
            return self.fail_permission(session, path, params, headers)

        # Check the size of the upload
        fp = params["deckupload"].file
        fp.seek(0, 2)
        size = fp.tell()
        fp.seek(0)
        if size > 200 * 1024:
            return (303,  # 303 See Other
                    {"Location": "/dashboard/filesizefail"},
                    "")

        # Create a new match
        match = Match()

        # Create the deck from the upload
        match.create_deck(fp.read().decode())

        # Add the participant to the match
        part = Participant(session["id"], session["nickname"])
        match.add_participant(part)

        # Make the match available for others
        match.put_in_pool()

        return (303,  # 303 See Other
                {"Location": "/match"},
                "")

    def match(self, session, path, params, headers):
        """Handles a request of the match view.

        Serves the match template.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        # Populate symbol table
        symtab = {"theme": session["theme"],
                  "showLogout": True if self._logout_shown else None}

        # Parse the template
        data = Parser.get_template("./res/tpl/match.html", symtab)
        return (200,  # 200 OK
                {"Content-Type": "text/html; charset=utf-8"},
                data)
