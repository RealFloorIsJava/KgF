"""
Part of KgF.

Author: LordKorea
"""

# Import controllers for leafs here
from pages.leafs.index import IndexController
from pages.leafs.resource import ResourceController


class Leafs:
    """
    Adds all leafs to the master controller.
    Leafs should be added in here.
    """

    @staticmethod
    def add_leafs(mctrl):
        """
        To register a leaf, add a line of the form
        > mctrl.add_leaf("test", TestController())
        """
        # Index controller, the default landing page
        mctrl.add_leaf("index", IndexController())
        # Resource loader for css/js/images
        mctrl.add_leaf("res", ResourceController())
