"""
Part of KgF.

Author: LordKorea
"""

from html import escape
from json import dumps
from time import time

from pages.controller import Controller
from server.match import Match


class APIController(Controller):
    """ Leaf /api """

    def __init__(self):
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

    def check_access(self, session, path, params, headers):
        """ Checks whether the user is logged in """
        return "login" in session

    def fail_permission(self, session, path, params, headers):
        """ Called when the user is not authorized """
        return (403,  # 403 Forbidden
                {"Content-Type": "application/json; charset=utf-8"},
                "{\"error\":\"not authenticated\"}")

    def api_pick(self, session, path, params, headers):
        """ Picks a winner """
        match = Match.get_match(session["id"])
        if match is None:
            return self.fail_permission(session, path, params, headers)
        part = match.get_participant(session["id"])

        if not match.is_picking() or not part.is_picking():
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
        """ Chooses / unchooses a hand card """
        match = Match.get_match(session["id"])
        if match is None:
            return self.fail_permission(session, path, params, headers)
        part = match.get_participant(session["id"])

        if not match.is_choosing() or part.is_picking():
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
        """ Retrieves the list of cards (hand, played) in the current match """
        match = Match.get_match(session["id"])
        if match is None:
            return self.fail_permission(session, path, params, headers)
        part = match.get_participant(session["id"])

        data = {"hand": {"OBJECT": {},
                         "VERB": {}},
                "played": {}}

        # Load the data of the hand cards
        hand = part.get_hand()
        for id in hand:
            data["hand"][hand[id][0]][id] = {"text": hand[id][1],
                                             "chosen": hand[id][2]}

        # Load the data of the played cards
        for p in match.get_participants():
            redacted = not match.can_view_choices() and part is not p
            data["played"][p.get_order()] = p.get_choose_data(redacted)

        return (200,  # 200 OK
                {"Content-Type": "application/json; charset=utf-8"},
                dumps(data))

    def api_participants(self, session, path, params, headers):
        """ Retrieves the list of participants in the current match """
        match = Match.get_match(session["id"])
        if match is None:
            return self.fail_permission(session, path, params, headers)

        data = []
        for part in match.get_participants():
            data.append({"id": part.get_id(),
                         "name": part.get_nickname(),
                         "score": part.get_score(),
                         "picking": part.is_picking()})

        return (200,  # 200 OK
                {"Content-Type": "application/json; charset=utf-8"},
                dumps(data))

    def api_chat_send(self, session, path, params, headers):
        """ Sends a chat message """
        msg = escape(params["message"])
        match = Match.get_match(session["id"])
        if match is None:
            return self.fail_permission(session, path, params, headers)
        part = match.get_participant(session["id"])

        # Check whether the user may send a message now
        if "chatcooldown" in session:
            if session["chatcooldown"] > time():
                return {403,  # 403 Forbidden
                        {"Content-Type": "application/json; charset=utf-8"},
                        "{\"status\":\"spam rejected\"}"}
        session["chatcooldown"] = time() + 1

        # Check the chat message for sanity
        if len(msg) > 0 and len(msg) < 200:
            # Send the message
            nick = part.get_nickname()
            match.send_message(nick, msg)
            return (200,  # 200 OK
                    {"Content-Type": "application/json; charset=utf-8"},
                    "{\"status\":\"sent\"}")

        return (403,  # 403 Forbidden
                {"Content-Type": "application/json; charset=utf-8"},
                "{\"status\":\"invalid size\"}")

    def api_chat(self, session, path, params, headers):
        """
        Retrieves the chat history (either the complete history or starting
        at the given offset)
        """
        match = Match.get_match(session["id"])
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
        """ Retrieves the status of the current match """
        match = Match.get_match(session["id"])
        if match is None:
            return self.fail_permission(session, path, params, headers)
        part = match.get_participant(session["id"])

        # Refresh the timeout timer of the participant
        part.refresh()

        # Prepare the data for the status request
        data = {"timer": int(match.get_seconds_to_next_phase()),
                "status": match.get_status(),
                "ending": match.is_ending(),
                "hasCard": match.has_card(),
                "allowChoose": match.is_choosing() and not part.is_picking(),
                "allowPick": match.is_picking() and part.is_picking(),
                "gaps": match.count_gaps()}

        # Add the card text to the output, if possible
        if data["hasCard"]:
            data["cardText"] = match.get_card()[1]

        return (200,  # 200 OK
                {"Content-Type": "application/json; charset=utf-8"},
                dumps(data))

    def api_list(self, session, path, params, headers):
        """ Returns the list of matches """
        data = []
        matches = Match.get_all()
        for match in matches:
            data.append({
                "id": match.get_id(),
                "owner": match.get_owner_nick(),
                "participants": match.get_num_participants(),
                "started": match.has_started(),
                "seconds": int(match.get_seconds_to_next_phase())
            })
        return (200,  # 200 OK
                {"Content-Type": "application/json; charset=utf-8"},
                dumps(data))
