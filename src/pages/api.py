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
from json import dumps
from time import time
from typing import Any, Dict

from model.match import ExpectationException, Match
from model.participant import Participant
from nussschale.leafs.controller import Controller
from nussschale.leafs.endpoint import AccessRestriction, Endpoint, \
    EndpointContext, HTTPException, PermissionFailHandler, RequireParameters, \
    RequirePath


# Handles the /api leaf.
APILeaf = Controller()


@AccessRestriction(APILeaf)
def check_login(ctx: EndpointContext) -> bool:
    """Checks whether the user is logged in.

    Args:
        ctx: The context of the request.

    Returns:
        Whether the client is logged in.
    """
    return "login" in ctx.session


@PermissionFailHandler(APILeaf)
def access_denied(_: EndpointContext) -> None:
    """Handles unauthorized clients.

    Args:
        _: The context of the request.

    Raises:
        HTTPException: (403) Always.
    """
    raise HTTPException.forbidden(True)


@Endpoint(APILeaf)
@RequirePath("join")
@RequireParameters("spectator", "id")
def api_join(ctx: EndpointContext) -> None:
    """Handles joining a match.

    Args:
        ctx: The context of the request.

    Raises:
        HTTPException: (403) When the user is already in a match,
                             or invalid data is sent.
    """
    if Match.get_match_of_player(ctx.session["id"]) is not None:
        # The user is already in a match
        raise HTTPException.forbidden(True)

    # Get the match ID and participant state
    try:
        id = int(ctx.params["id"])  # type: ignore
    except ValueError:
        raise HTTPException.forbidden(True)
    spectator = ctx.params["spectator"] == "true"

    # Get the match
    match = Match.get_by_id(id)
    if match is None:
        raise HTTPException.forbidden(True)

    # Put the player into the match
    part = Participant(ctx.session["id"], ctx.session["nickname"])
    part.spectator = spectator
    try:
        match.add_participant(part)
    except ExpectationException:
        # Can't join right now
        raise HTTPException.forbidden(True)

    ctx.json_ok()


@Endpoint(APILeaf)
@RequirePath("pick")
@RequireParameters("playedId")
def api_pick(ctx: EndpointContext) -> None:
    """Handles picking a round winner.

    Args:
        ctx: The context of the request.

    Raises:
        HTTPException: (403) When the user is not in a match,
                             or invalid data is sent.
    """
    match = Match.get_match_of_player(ctx.session["id"])
    if match is None:
        raise HTTPException.forbidden(True)

    # Get the participant. Participant must not be a spectator.
    part = match.get_participant(ctx.session["id"])
    if part.spectator:
        raise HTTPException.forbidden(True)

    # Check whether the participant is allowed to pick a winner.
    if not match.is_picking() or not part.picking:
        raise HTTPException.forbidden(True)

    # Pick the winner.
    try:
        playedid = int(ctx.params["playedId"])  # type: ignore
    except ValueError:
        raise HTTPException.forbidden(True)
    match.declare_round_winner(playedid)
    ctx.json_ok()


@Endpoint(APILeaf)
@RequirePath("choose")
@RequireParameters("handId")
def api_choose(ctx: EndpointContext) -> None:
    """Handles (un)choosing a hand card.

    Args:
        ctx: The context of the request.

    Raises:
        HTTPException: (403) When the user is not in a match,
                             or invalid data is sent.
    """
    match = Match.get_match_of_player(ctx.session["id"])
    if match is None:
        raise HTTPException.forbidden(True)
    part = match.get_participant(ctx.session["id"])
    if part.spectator:
        raise HTTPException.forbidden(True)

    if not match.is_choosing() or part.picking:
        raise HTTPException.forbidden(True)

    try:
        handid = int(ctx.params["handId"])  # type: ignore
    except ValueError:
        raise HTTPException.forbidden(True)

    part.toggle_chosen(handid, match.count_gaps())
    match.check_choosing_done()
    ctx.json_ok()


@Endpoint(APILeaf)
@RequirePath("cards")
def api_cards(ctx: EndpointContext) -> None:
    """Retrieves the list of cards (hand, played) in the current match.

    Returns a JSON response containing the hand cards and played cards.

    Args:
        ctx: The context of the request.

    Raises:
        HTTPException: (403) When the user is not in a match,
                             or invalid data is sent.
    """
    match = Match.get_match_of_player(ctx.session["id"])
    if match is None:
        raise HTTPException.forbidden(True)
    part = match.get_participant(ctx.session["id"])

    data = {}

    # Load the data of the hand cards
    if not part.spectator:
        hand_cards = {
            "OBJECT": {},
            "VERB": {}
        }  # type: Dict[str, Dict]
        hand = part.get_hand()
        for id, hcard in hand.items():
            hand_cards[hcard.card.type][id] = {"text": hcard.card.text,
                                               "chosen": hcard.chosen}
        data["hand"] = hand_cards

    # Load the data of the played cards
    # Note: If the order changes this might lead to inconsistencies but the
    # client polls this data often so it is no problem.
    played_cards = []  # type: Any
    can_view_choices = match.can_view_choices()
    for p in match.get_participants(False):
        redacted = not can_view_choices and part is not p
        order = p.order

        # Ensure list is big enough then insert the data
        while len(played_cards) <= order:
            played_cards.append([])
        played_cards[p.order] = p.get_choose_data(redacted)
    data["played"] = played_cards

    ctx.ok("application/json; charset=utf-8", dumps(data))


@Endpoint(APILeaf)
@RequirePath("participants")
def api_participants(ctx: EndpointContext) -> None:
    """Retrieves the list of participants of the client's match.

    Returns a JSON response containing the participants of the match.

    Args:
        ctx: The context of the request.

    Raises:
        HTTPException: (403) When the user is not in a match,
                             or invalid data is sent.
    """
    match = Match.get_match_of_player(ctx.session["id"])
    if match is None:
        raise HTTPException.forbidden(True)

    data = []
    for part in match.get_participants():
        data.append({"id": part.id,
                     "name": part.nickname,
                     "score": part.score,
                     "picking": part.picking,
                     "spectator": part.spectator})

    ctx.ok("application/json; charset=utf-8", dumps(data))


@Endpoint(APILeaf)
@RequirePath("chat", "send")
@RequireParameters("message")
def api_chat_send(ctx: EndpointContext) -> None:
    """Handles sending a chat message.

    Args:
        ctx: The context of the request.

    Raises:
        HTTPException: (403) When the user is not in a match,
                             or invalid data is sent.
    """
    if not isinstance(ctx.params["message"], str):
        raise HTTPException.forbidden(True)
    msg = escape(ctx.params["message"])
    match = Match.get_match_of_player(ctx.session["id"])
    if match is None:
        raise HTTPException.forbidden(True)
    part = match.get_participant(ctx.session["id"])

    # Check whether the user may send a message now
    if "chatcooldown" in ctx.session:
        if ctx.session["chatcooldown"] > time():
            ctx.code = 403  # 403 Forbidden
            ctx.response_headers["Content-Type"] = ("application/json;"
                                                    " charset=utf-8")
            ctx.response = dumps({"error": "spam rejected"})
            return
    ctx.session["chatcooldown"] = time() + 1

    # Check the chat message for sanity
    if 0 < len(msg) < 200:
        # Send the message
        match.send_message(part.nickname, msg)
        ctx.json_ok()
    else:
        ctx.code = 403  # 403 Forbidden
        ctx.response_headers["Content-Type"] = ("application/json;"
                                                " charset=utf-8")
        ctx.response = dumps({"error": "invalid size"})


@Endpoint(APILeaf)
@RequirePath("chat")
def api_chat(ctx: EndpointContext) -> None:
    """Retrieves the chat history, optionally starting at the given offset.

    Returns a JSON response containing the requested chat messages.

    Args:
        ctx: The context of the request.

    Raises:
        HTTPException: (403) When the user is not in a match,
                             or invalid data is sent.
    """
    match = Match.get_match_of_player(ctx.session["id"])
    if match is None:
        raise HTTPException.forbidden(True)

    # Check whether a message offset was supplied
    offset = 0
    if "offset" in ctx.params:
        try:
            offset = int(ctx.params["offset"])  # type: ignore
        except ValueError:
            pass

    # Fetch the chat data
    data = match.retrieve_chat(offset)
    ctx.ok("application/json; charset=utf-8", dumps(data))


@Endpoint(APILeaf)
@RequirePath("status")
def api_status(ctx: EndpointContext) -> None:
    """Retrieves the status of the client's match.

    Returns a JSON response containing the status.

    Args:
        ctx: The context of the request.

    Raises:
        HTTPException: (403) When the user is not in a match,
                             or invalid data is sent.
    """
    match = Match.get_match_of_player(ctx.session["id"])
    if match is None:
        raise HTTPException.forbidden(True)
    part = match.get_participant(ctx.session["id"])

    # Refresh the timeout timer of the participant
    part.refresh()

    # Prepare the data for the status request
    allow_choose = (match.is_choosing()
                    and not part.picking
                    and not part.spectator)
    allow_pick = (match.is_picking()
                  and part.picking
                  and not part.spectator)
    data = {"timer": int(match.get_seconds_to_next_phase()),
            "status": match.get_status(),
            "ending": match.is_ending(),
            "hasCard": match.has_card(),
            "allowChoose": allow_choose,
            "allowPick": allow_pick,
            "isSpectator": part.spectator,
            "gaps": match.count_gaps()}

    # Add the card text to the output, if possible
    if data["hasCard"]:
        data["cardText"] = match.current_card.text

    ctx.ok("application/json; charset=utf-8", dumps(data))


@Endpoint(APILeaf)
@RequirePath("list")
def api_list(ctx: EndpointContext) -> None:
    """Retrieves the list of all existing matches.

    Returns a JSON response containing all matches.

    Args:
        ctx: The context of the request.

    Raises:
        HTTPException: (403) When the user is not in a match,
                             or invalid data is sent.
    """
    data = []
    matches = Match.get_all()
    for match in matches:
        data.append({
            "id": match.id,
            "owner": match.get_owner_nick(),
            "participants": match.get_num_participants(),
            "canJoin": match.can_join(),
            "seconds": int(match.get_seconds_to_next_phase())
        })
    ctx.ok("application/json; charset=utf-8", dumps(data))
