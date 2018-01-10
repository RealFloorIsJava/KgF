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

from random import randint
from typing import Any
from uuid import uuid4

from nussschale.leafs.controller import Controller
from nussschale.leafs.endpoint import Endpoint, EndpointContext, \
    HTTPException, OnlyIf, RequireParameters, RequirePath
from nussschale.nussschale import nconfig
from nussschale.session import SessionData
from nussschale.util.template import Parser


def _create_user(session: SessionData) -> None:
    """Initializes a temporary user account.

    Args:
        session: The session data the user will be created in.
    """
    session["login"] = True
    session["id"] = str(uuid4())
    session["nickname"] = "Meme" + str(randint(10000, 99999))
    session["theme"] = "light"


class IndexController(Controller):
    """Handles the /index leaf.

    Class Attributes:
        login_pw: The login password.
        login_required: Whether login is required.
    """

    # Load the login password
    login_pw = nconfig().get("site-pw", "loremipsum")

    # Whether a login is required
    login_required = nconfig().get("login-required", True)


IndexLeaf = IndexController()


@Endpoint(IndexLeaf)
@OnlyIf(not IndexController.login_required)
def no_login_required(ctx: EndpointContext) -> None:
    """Handles creating a user when login is disabled.

    Will redirect to the dashboard.

    Args:
        ctx: The request's context.

    Raises:
        HTTPException: (303) Always.
    """
    if "login" not in ctx.session:
        _create_user(ctx.session)
    raise HTTPException.see_other().redirect("/dashboard")


@Endpoint(IndexLeaf)
@RequireParameters("pw")
def login(ctx: EndpointContext) -> None:
    """Handles requests made with the login form.

    Will redirect to the dashboard on success.
    If the login fails the client is redirected to the index endpoint.

    Args:
        ctx: The request's context.

    Raises:
        HTTPException: (303) Always.
    """
    if ctx.params["pw"] == IndexController.login_pw:
        _create_user(ctx.session)
        raise HTTPException.see_other().redirect("/dashboard")
    raise HTTPException.see_other().redirect("/index/pwfail")


@Endpoint(IndexLeaf)
@RequirePath("logout")
def logout(ctx: EndpointContext) -> None:
    """Handles logout requests.

    Will show the index page (via the index endpoint).

    Args:
        ctx: The context of the request.
    """
    if "login" in ctx.session:
        ctx.session.remove("login")
    index(ctx)


@Endpoint(IndexLeaf)
def index(ctx: EndpointContext) -> None:
    """Handles requests for the index page.

    Redirects to the dashboard if the client is logged in. Serves the
    start template otherwise.

    Args:
        ctx: The context of the request.

    Raises:
        HTTPException: (303) When logged in.
    """
    if "login" in ctx.session:
        raise HTTPException.see_other().redirect("/dashboard")

    # Populate symbol table
    symtab = {}  # type: Any
    msg_indicators = ["authfail", "pwfail", "logout"]
    for ind in msg_indicators:
        if ind in ctx.path:
            symtab[ind] = ""

    # Parse the template
    data = Parser.get_template("./res/tpl/start.html", symtab)
    ctx.ok("text/html; charset=utf-8", data)
