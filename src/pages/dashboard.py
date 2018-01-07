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

from nussschale.leafs.controller import Controller
from nussschale.leafs.endpoint import AccessRestriction, Endpoint, \
    EndpointContext, HTTPException, PermissionFailHandler
from nussschale.nussschale import nconfig
from nussschale.util.template import Parser


class DashboardController(Controller):
    """Handles the /dashboard leaf.

    Class Attributes:
        logout_shown: Whether the logout link is shown, i.e.
    """

    # Whether the logout link will be shown
    logout_shown = nconfig().get("login-required", True)


DashboardLeaf = DashboardController()


@AccessRestriction(DashboardLeaf)
def check_login(ctx: EndpointContext) -> bool:
    """Checks whether the user is logged in.

    Args:
        ctx: The context of the request.

    Returns:
        Whether the client is logged in.
    """
    return "login" in ctx.session


@PermissionFailHandler(DashboardLeaf)
def access_denied(_: EndpointContext):
    """Handles unauthorized clients.

    Args:
        _: The context of the request.

    Raises:
        HTTPException: (303) Always.
    """
    raise HTTPException.see_other().redirect("/index/authfail")


@Endpoint(DashboardLeaf)
def dashboard(ctx: EndpointContext):
    """Handles requests for the dashboard page.

    Serves the dashboard template.

    Args:
        ctx: The context of the request.
    """
    # Populate symbol table
    symtab = {"nickname": ctx.session["nickname"],
              "theme": ctx.session["theme"],
              "showLogout": True if DashboardController.logout_shown else None}

    # Check for deck upload errors
    deck_errors = ["deck_too_big", "invalid_format", "invalid_type",
                   "illegal_gap", "too_many_gaps", "statement_no_gap",
                   "deck_too_small"]
    for err in deck_errors:
        if err in ctx.path:
            symtab[err] = ""

    # Parse the template
    data = Parser.get_template("./res/tpl/dashboard.html", symtab)
    ctx.ok("text/html; charset=utf-8", data)
