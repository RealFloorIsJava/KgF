"""
Part of KgF.

Author: LordKorea
"""

from html import escape

from pages.controller import Controller


class OptionsController(Controller):
    """ Leaf /options """

    def __init__(self):
        super().__init__()

        # Only allow logged-in users
        self.add_access_restriction(self.check_access)
        self.set_permission_fail_handler(self.fail_permission)

        self.add_endpoint(self.theme, params_restrict={"theme"})
        self.add_endpoint(self.name, params_restrict={"name"})

    def check_access(self, session, path, params, headers):
        """ Checks whether the user is logged in """
        return "login" in session

    def fail_permission(self, session, path, params, headers):
        """ Called when the user is not authorized """
        return (403,  # 403 Forbidden
                {"Content-Type": "text/plain"},
                "Not authenticated")

    def theme(self, session, path, params, headers):
        """ Handles changes of the theme """
        new_theme = params["theme"]
        if new_theme not in ("dark", "light"):
            new_theme = "light"
        session["theme"] = new_theme
        return (200,  # 200 OK
                {"Content-Type": "text/plain"},
                "OK")

    def name(self, session, path, params, headers):
        """ Handles changes of the nickname """
        new_name = escape(params["name"])[:31]
        session["nickname"] = new_name
