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

from html import escape

from pages.controller import Controller


class OptionsController(Controller):
    """Handles the /options leaf."""

    def __init__(self):
        """Constructor."""
        super().__init__()

        # Only allow logged-in users
        self.add_access_restriction(self.check_access)
        self.set_permission_fail_handler(self.fail_permission)

        self.add_endpoint(self.theme, params_restrict={"theme"})
        self.add_endpoint(self.name, params_restrict={"name"})

    def check_access(self, session, path, params, headers):
        """Checks whether the user is logged in.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            bool: True if and only if the user is logged in.
        """
        return "login" in session

    def fail_permission(self, session, path, params, headers):
        """Handles unauthorized clients.

        Informs the client that access was denied.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        return (403,  # 403 Forbidden
                {"Content-Type": "text/plain"},
                "Not authenticated")

    def theme(self, session, path, params, headers):
        """Handles changing the theme of the application for a client.

        The theme is set to either 'light' or 'dark', depending on the request
        parameters.
        Informs the client of the success of the operation.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        new_theme = params["theme"]
        if new_theme not in ("dark", "light"):
            new_theme = "light"
        session["theme"] = new_theme
        return (200,  # 200 OK
                {"Content-Type": "text/plain"},
                "OK")

    def name(self, session, path, params, headers):
        """Handles changing the name of the client.

        If the name is longer than 31 characters it will be cut off after
        the 31st character.
        Informs the client of the success of the operation.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        new_name = escape(params["name"])[:31]
        session["nickname"] = new_name
        return (200,  # 200 OK
                {"Content-Type": "text/plain"},
                "OK")
