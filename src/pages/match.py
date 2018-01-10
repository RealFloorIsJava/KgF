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

from typing import Any, cast

from model.match import Match
from model.participant import Participant
from nussschale.leafs.controller import Controller
from nussschale.leafs.endpoint import AccessRestriction, Endpoint, \
    EndpointContext, HTTPException, PermissionFailHandler, RequireParameters, \
    RequirePath
from nussschale.nussschale import nconfig
from nussschale.util.template import Parser


class MatchController(Controller):
    """Handles the /match leaf.

    Class Attributes:
        logout_shown: Whether the logout link is shown. This is True if login
            is enabled in the configuration.
    """

    # Whether the logout link will be shown
    logout_shown = nconfig().get("login-required", True)


MatchLeaf = MatchController()


@AccessRestriction(MatchLeaf)
def require_login(ctx: EndpointContext) -> bool:
    """Checks whether the user is logged in.

    Args:
        ctx: The context of the request.

    Returns:
        True iff the client is logged in.
    """
    return "login" in ctx.session


@AccessRestriction(MatchLeaf)
def require_in_match(ctx: EndpointContext) -> bool:
    """Checks whether the user is in a match (or does not need to be in one).

    Args:
        ctx: The context of the request.

    Returns:
        True iff the client is in a match or does not need to be in one.
    """
    is_exempt = "create" in ctx.path
    return (is_exempt
            or Match.get_match_of_player(ctx.session["id"]) is not None)


@PermissionFailHandler(MatchLeaf)
def access_denied(_: EndpointContext) -> None:
    """Redirects the client to the dashboard when access is denied.

    Args:
        _: Ignored.

    Raises:
        HTTPException: (303) Always.
    """
    raise HTTPException.see_other().redirect("/dashboard")


@Endpoint(MatchLeaf)
@RequirePath("create")
@RequireParameters("deckupload")
def create_match(ctx: EndpointContext) -> None:
    """Handles the request to create a match.

    Redirects either to the match view (on success) or to the dashboard
    (when the deck is too big or another error occurs).

    Args:
        ctx: The context of the request.

    Raises:
        HTTPException: (303) When a user-error occurs or on success.
                       (415) When the data sent is invalid.
    """
    if Match.get_match_of_player(ctx.session["id"]) is not None:
        # The user already is in a match
        raise HTTPException.see_other().redirect("/match")

    # Make sure the uploaded thing is a file
    deckupload = cast(Any, ctx.params["deckupload"])
    if not deckupload.filename:
        raise HTTPException.unsupported_media_type()

    # Check the size of the upload
    fp = deckupload.file
    fp.seek(0, 2)
    size = fp.tell()
    fp.seek(0)
    if size > 800 * 1000:
        raise HTTPException.see_other().redirect("/dashboard/deck_too_big")

    # Create a new match
    match = Match()

    # Create the deck from the upload
    try:
        data = fp.read().decode()
    except UnicodeDecodeError:
        raise HTTPException.unsupported_media_type()
    success, msg = match.create_deck(data)

    # Check for failure
    if not success:
        raise HTTPException.see_other().redirect("/dashboard/%s" % msg)

    # Add the participant to the match
    part = Participant(ctx.session["id"], ctx.session["nickname"])
    match.add_participant(part)

    # Make the match available for others
    match.put_in_pool()
    raise HTTPException.see_other().redirect("/match")


@Endpoint(MatchLeaf)
@RequirePath("create")
def insufficient_match_create(_: EndpointContext) -> None:
    """Redirects to the dashboard when a match creation lacks information.

    Args:
        _: Ignored.

    Raises:
        HTTPException: (303) Always.
    """
    raise HTTPException.see_other().redirect("/dashboard")


@Endpoint(MatchLeaf)
@RequirePath("abandon")
def abandon_match(ctx: EndpointContext) -> None:
    """Handles the request to abandon a match.

    Redirects the client to the dashboard.

    Raises:
        HTTPException: (303) Always.
    """
    # Leave the match
    match = Match.get_match_of_player(ctx.session["id"])
    match.abandon_participant(ctx.session["id"])
    raise HTTPException.see_other().redirect("/dashboard")


@Endpoint(MatchLeaf)
def match_view(ctx: EndpointContext) -> None:
    """Handles a request for the match view.

    Serves the match template.

    Args:
        ctx: The context of the request.
    """
    # Populate symbol table
    symtab = {"theme": ctx.session["theme"],
              "showLogout": "" if MatchController.logout_shown else None}

    # Parse the template
    data = Parser.get_template("./res/tpl/match.html", symtab)
    ctx.ok("text/html; charset=utf-8", data)
