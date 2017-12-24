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
        # Populate symbol table
        symtab = {}
        if "login" in session:
            symtab['login'] = True

        # Parse the template
        data = Parser.get_template("./res/tpl/start.html", symtab)
        return (200,  # 200 OK
                {"Content-Type": "text/html"},
                data)
