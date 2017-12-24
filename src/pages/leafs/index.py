"""
    Part of KgF.

    Author: LordKorea
"""

from pages.controller import Controller
from pages.templates.engine import Parser


class IndexController(Controller):
    """
        Leaf /index
    """

    def __init__(self):
        super().__init__()
        self.add_endpoint(self.index)

    def index(self, session, path, params, headers):
        """
            The index page /index
        """
        # Populate symbolic table
        symtab = {}
        if "login" in session:
            symtab['login'] = True

        # Parse the template
        data = Parser.get_template("./pages/templates/start.html", symtab)
        return (
            200,
            {"Content-Type": "text/html"},
            data
        )
