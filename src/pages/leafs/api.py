"""
Part of KgF.

Author: LordKorea
"""

from json import dumps

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

    def check_access(self, session, path, params, headers):
        """ Checks whether the user is logged in """
        return "login" in session

    def fail_permission(self, session, path, params, headers):
        """ Called when the user is not authorized """
        return (403,  # 403 Forbidden
                {"Content-Type": "application/json; charset=utf-8"},
                "{\"error\":\"not authenticated\"}")

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
