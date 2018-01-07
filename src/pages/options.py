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

from html import escape

from nussschale.leafs.controller import Controller
from nussschale.leafs.endpoint import AccessRestriction, Endpoint, \
    EndpointContext, HTTPException, PermissionFailHandler, RequireParameters


# The /option leaf
OptionsLeaf = Controller()


@AccessRestriction(OptionsLeaf)
def login_required(ctx: EndpointContext) -> bool:
    """Checks whether the user is logged in.

    Args:
        ctx: The context of the request.

    Returns:
        True iff the client is logged in.
    """
    return "login" in ctx.session


@PermissionFailHandler(OptionsLeaf)
def not_logged_in(_: EndpointContext):
    """Informs the client that access was denied.

    Args:
        _: Ignored.

    Raises:
        HTTPException: (403, json) Always.
    """
    raise HTTPException.forbidden(True)


@Endpoint(OptionsLeaf)
@RequireParameters("theme")
def theme(ctx: EndpointContext):
    """Handles changing the theme of the application for a client.

    The theme is set to either 'light' or 'dark', depending on the request
    parameters.
    Informs the client of the success of the operation.

    Args:
        ctx: The request's context.
    """
    new_theme = ctx.params["theme"]
    if new_theme not in ("dark", "light"):
        new_theme = "light"
    ctx.session["theme"] = new_theme
    ctx.json_ok()


@Endpoint(OptionsLeaf)
@RequireParameters("name")
def name(ctx: EndpointContext):
    """Handles changing the name of the client.

    If the name is longer than 31 characters it will be cut off after
    the 31st character.
    Informs the client of the success of the operation.

    Args:
        ctx: The request's context.
    """
    name_param = ctx.params["name"]
    if not isinstance(name_param, str):
        raise HTTPException.unsupported_media_type(True)
    new_name = escape(name_param)[:31]
    ctx.session["nickname"] = new_name
    ctx.json_ok()
