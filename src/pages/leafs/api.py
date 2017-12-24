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

        self.add_endpoint(self.api_matchlist, path_restrict={"matchlist"})

    def check_access(self, session, path, params, headers):
        """ Checks whether the user is logged in """
        return "login" in session

    def fail_permission(self, session, path, params, headers):
        """ Called when the user is not authorized """
        return (403,  # 403 Forbidden
                {"Content-Type": "application/json; charset=utf-8"},
                "{\"error\":\"not authenticated\"}")

    def api_matchlist(self, session, path, params, headers):
        """ Returns a list of matches """
        data = []
        matches = Match.get_all()
        for match in matches:
            data.append({
                "id": match.get_id(),
                "owner": match.get_owner_nick(),
                "participants": match.get_num_participants(),
                "started": match.has_started(),
                "seconds": match.get_seconds_to_next_phase()
            })
        return (200,  # 200 OK
                {"Content-Type": "application/json; charset=utf-8"},
                dumps(data))
