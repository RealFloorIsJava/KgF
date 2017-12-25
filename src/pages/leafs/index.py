"""
Part of KgF.

Author: LordKorea
"""

from random import randint
from uuid import uuid4

from kgf import kconfig
from pages.controller import Controller
from pages.templates.engine import Parser


class IndexController(Controller):
    """ Leaf /index """

    def __init__(self):
        super().__init__()

        # Load the login password
        self._login_pw = kconfig().get("site-pw", "loremipsum")

        self.add_endpoint(self.login, params_restrict={"pw"})
        self.add_endpoint(self.logout, path_restrict={"logout"})
        self.add_endpoint(self.index)

    def login(self, session, path, params, headers):
        """ Handles the login form """
        if params["pw"] == self._login_pw:
            session["login"] = True
            session["id"] = str(uuid4())
            session["nickname"] = "Meme" + str(randint(10000, 99999))
            session["theme"] = "light"
            return None  # fall through (will redirect to dashboard)
        return (303,  # 303 See Other
                {"Location": "/index/pwfail"},
                "")

    def logout(self, session, path, params, headers):
        """ Handles logout requests """
        if "login" in session:
            session.remove("login")

        return None  # Fall through

    def index(self, session, path, params, headers):
        """ The index page /index """
        # If the user is already logged in, send him to the dashboard
        if "login" in session:
            return (303,  # 303 See Other
                    {"Location": "/dashboard"},
                    "")

        # Populate symbol table
        symtab = {}
        if "authfail" in path:
            symtab["authfail"] = True
        elif "pwfail" in path:
            symtab["pwfail"] = True
        elif "logout" in path:
            symtab["logout"] = True

        # Parse the template
        data = Parser.get_template("./res/tpl/start.html", symtab)
        return (200,  # 200 OK
                {"Content-Type": "text/html; charset=utf-8"},
                data)
