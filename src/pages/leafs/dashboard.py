"""
Part of KgF.

Author: LordKorea
"""

from pages.controller import Controller
from pages.templates.engine import Parser


class DashboardController(Controller):
    """
    Leaf /dashboard
    """

    def __init__(self):
        super().__init__()

        # Only allow logged-in users
        self.add_access_restriction(self.check_access)
        self.set_permission_fail_handler(self.fail_permission)

        self.add_endpoint(self.dashboard)

    def check_access(self, session, path, params, headers):
        """
        Checks whether the user is logged in
        """
        return "login" in session

    def fail_permission(self, session, path, params, headers):
        """
        Called when the user is not authorized
        """
        return (303,  # 303 See Other
                {"Location": "/index/authfail"},
                "")

    def dashboard(self, session, path, params, headers):
        """
        The dashboard page /dashboard
        """
        # Populate symbol table
        symtab = {
            "nickname": session["nickname"],
            "theme": session["theme"]
        }

        # Parse the template
        data = Parser.get_template("./res/tpl/dashboard.html", symtab)
        return (200,  # 200 OK
                {"Content-Type": "text/html; charset=utf-8"},
                data)
