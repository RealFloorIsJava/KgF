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


class DeckeditController(Controller):
    """Handles the /deckedit leaf.

    Class Attributes:
        logout_shown: Whether the logout link is shown, i.e. whether login is
            required.
    """

    # Whether the logout link will be shown
    logout_shown = nconfig().get("login-required", True)


DeckeditLeaf = DeckeditController()


@AccessRestriction(DeckeditLeaf)
def check_login(ctx: EndpointContext) -> bool:
    """Checks whether the user is logged in.

    Args:
        ctx: The context of the request.

    Returns:
        Whether the client is logged in.
    """
    return "login" in ctx.session


@PermissionFailHandler(DeckeditLeaf)
def access_denied(_: EndpointContext):
    """Handles unauthorized clients.

    Args:
        _: The context of the request.

    Raises:
        HTTPException: (303) Always.
    """
    raise HTTPException.see_other().redirect("/index/authfail")


@Endpoint(DeckeditLeaf)
def deckedit(ctx: EndpointContext):
    """Handles requests for the deck editor page.

    Serves the deck editor template.

    Args:
        ctx: The request's context.
    """
    # Populate symbol table
    symtab = {"nickname": ctx.session["nickname"],
              "theme": ctx.session["theme"],
              "showLogout": "" if DeckeditController.logout_shown else None}

    # Parse the template
    data = Parser.get_template("./res/tpl/deckedit.html", symtab)
    ctx.ok("text/html; charset=utf-8", data)
