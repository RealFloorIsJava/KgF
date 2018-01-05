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

from model.match import ExpectationException, Match
from model.participant import Participant
from pages.controller import Controller


class APIController(Controller):
    """Handles the /api leaf."""

    def __init__(self):
        """Constructor."""
        super().__init__()

        # Only allow logged-in users
        self.add_access_restriction(self.check_access)
        self.set_permission_fail_handler(self.fail_permission)

        self.add_endpoint(self.api_list, path_restrict={"list"})
        self.add_endpoint(self.api_status, path_restrict={"status"})
        self.add_endpoint(self.api_chat_send,
                          path_restrict={"chat", "send"},
                          params_restrict={"message"})
        self.add_endpoint(self.api_chat, path_restrict={"chat"})
        self.add_endpoint(self.api_participants,
                          path_restrict={"participants"})
        self.add_endpoint(self.api_cards, path_restrict={"cards"})
        self.add_endpoint(self.api_choose,
                          path_restrict={"choose"},
                          params_restrict={"handId"})
        self.add_endpoint(self.api_pick,
                          path_restrict={"pick"},
                          params_restrict={"playedId"})
        self.add_endpoint(self.api_join,
                          path_restrict={"join"},
                          params_restrict={"spectator", "id"})

    def check_access(self, session, path, params, headers):
        """Checks whether the user is logged in.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            bool: True if and only if the user is logged in.
        """
        return "login" in session

    def fail_permission(self, session, path, params, headers):
        """Handles unauthorized clients.

        Informs the client that access was denied.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        return (403,  # 403 Forbidden
                {"Content-Type": "application/json; charset=utf-8"},
                "{\"error\":\"not authenticated\"}")

    def api_join(self, session, path, params, headers):
        """Handles joining a match.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        if Match.get_match_of_player(session["id"]) is not None:
            # The user already is in a match
            return (303,  # 303 See Other
                    {"Location": "/match"},
                    "")

        # Get the match ID and participant state
        try:
            id = int(params["id"])
        except ValueError:
            return self.fail_permission(session, path, params, headers)
        spectator = params["spectator"] == "true"

        # Get the match
        match = Match.get_by_id(id)
        if match is None:
            return self.fail_permission(session, path, params, headers)

        # Put the player into the match
        part = Participant(session["id"], session["nickname"])
        part.spectator = spectator
        try:
            match.add_participant(part)
        except ExpectationException:  # Can't join right now
            return self.fail_permission(session, path, params, headers)

        return (303,  # 303 See Other
                {"Location": "/match"},
                "")

    def api_pick(self, session, path, params, headers):
        """Handles picking a round winner.

        Returns a JSON status.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        match = Match.get_match_of_player(session["id"])
        if match is None:
            return self.fail_permission(session, path, params, headers)
        part = match.get_participant(session["id"])
        if part.spectator:
            return self.fail_permission(session, path, params, headers)

        if not match.is_picking() or not part.picking:
            return self.fail_permission(session, path, params, headers)

        try:
            playedid = int(params["playedId"])
        except ValueError:
            return self.fail_permission(session, path, params, headers)

        match.declare_round_winner(playedid)

        return (200,  # 200 OK
                {"Content-Type": "application/json; charset=utf-8"},
                "{\"error\":\"OK\"}")

    def api_choose(self, session, path, params, headers):
        """Handles (un)choosing a hand card.

        Returns a JSON status.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        match = Match.get_match_of_player(session["id"])
        if match is None:
            return self.fail_permission(session, path, params, headers)
        part = match.get_participant(session["id"])
        if part.spectator:
            return self.fail_permission(session, path, params, headers)

        if not match.is_choosing() or part.picking:
            return self.fail_permission(session, path, params, headers)

        try:
            handid = int(params["handId"])
        except ValueError:
            return self.fail_permission(session, path, params, headers)

        part.toggle_chosen(handid, match.count_gaps())
        match.check_choosing_done()

        return (200,  # 200 OK
                {"Content-Type": "application/json; charset=utf-8"},
                "{\"error\":\"OK\"}")

    def api_cards(self, session, path, params, headers):
        """Retrieves the list of cards (hand, played) in the current match.

        Returns a JSON response containing the hand cards and played cards.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        match = Match.get_match_of_player(session["id"])
        if match is None:
            return self.fail_permission(session, path, params, headers)
        part = match.get_participant(session["id"])

        data = {}

        # Load the data of the hand cards
        if not part.spectator:
            hand_cards = {"OBJECT": {}, "VERB": {}}
            hand = part.get_hand()
            for id in hand:
                hcard = hand[id]
                hand_cards[hcard.card.type][id] = {"text": hcard.card.text,
                                                   "chosen": hcard.chosen}
            data["hand"] = hand_cards

        # Load the data of the played cards
        # Note: If the order changes this might lead to inconsistencies but the
        # client polls this data often so it is no problem.
        played_cards = []
        can_view_choices = match.can_view_choices()
        for p in match.get_participants():
            if p.spectator:
                continue

            redacted = not can_view_choices and part is not p
            order = p.order

            # Ensure list is big enough
            while len(played_cards) <= order:
                played_cards.append([])

            played_cards[p.order] = p.get_choose_data(redacted)
        data["played"] = played_cards

        return (200,  # 200 OK
                {"Content-Type": "application/json; charset=utf-8"},
                dumps(data))

    def api_participants(self, session, path, params, headers):
        """Retrieves the list of participants of the client's match.

        Returns a JSON response containing the participants of the match.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        match = Match.get_match_of_player(session["id"])
        if match is None:
            return self.fail_permission(session, path, params, headers)

        data = []
        for part in match.get_participants():
            data.append({"id": part.id,
                         "name": part.nickname,
                         "score": part.score,
                         "picking": part.picking,
                         "spectator": part.spectator})

        return (200,  # 200 OK
                {"Content-Type": "application/json; charset=utf-8"},
                dumps(data))

    def api_chat_send(self, session, path, params, headers):
        """Handles sending a chat message.

        Returns a JSON status.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        msg = escape(params["message"])
        match = Match.get_match_of_player(session["id"])
        if match is None:
            return self.fail_permission(session, path, params, headers)
        part = match.get_participant(session["id"])

        # Check whether the user may send a message now
        if "chatcooldown" in session:
            if session["chatcooldown"] > time():
                return {403,  # 403 Forbidden
                        {"Content-Type": "application/json; charset=utf-8"},
                        "{\"error\":\"spam rejected\"}"}
        session["chatcooldown"] = time() + 1

        # Check the chat message for sanity
        if 0 < len(msg) < 200:
            # Send the message
            match.send_message(part.nickname, msg)
            return (200,  # 200 OK
                    {"Content-Type": "application/json; charset=utf-8"},
                    "{\"error\":\"OK\"}")

        return (403,  # 403 Forbidden
                {"Content-Type": "application/json; charset=utf-8"},
                "{\"error\":\"invalid size\"}")

    def api_chat(self, session, path, params, headers):
        """Retrieves the chat history, optionally starting at the given offset.

        Returns a JSON response containing the requested chat messages.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        match = Match.get_match_of_player(session["id"])
        if match is None:
            return self.fail_permission(session, path, params, headers)

        # Check whether a message offset was supplied
        offset = 0
        if "offset" in params:
            try:
                offset = int(params["offset"])
            except ValueError:
                pass

        # Fetch the chat data
        data = match.retrieve_chat(offset)

        return (200,  # 200 OK
                {"Content-Type": "application/json; charset=utf-8"},
                dumps(data))

    def api_status(self, session, path, params, headers):
        """Retrieves the status of the client's match.

        Returns a JSON response containing the status.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        match = Match.get_match_of_player(session["id"])
        if match is None:
            return self.fail_permission(session, path, params, headers)
        part = match.get_participant(session["id"])

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

        return (200,  # 200 OK
                {"Content-Type": "application/json; charset=utf-8"},
                dumps(data))

    def api_list(self, session, path, params, headers):
        """Retrieves the list of all existing matches.

        Returns a JSON response containing all matches.

        Args:
            session (obj): The session data of the client.
            path (list): The path of the request.
            params (dict): The HTTP POST parameters.
            headers (dict): The HTTP headers that were sent by the client.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
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
        return (200,  # 200 OK
                {"Content-Type": "application/json; charset=utf-8"},
                dumps(data))
