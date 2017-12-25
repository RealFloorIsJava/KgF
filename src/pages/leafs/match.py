"""
Part of KgF.

Author: LordKorea
"""

from pages.controller import Controller
from pages.templates.engine import Parser
from server.match import Match
from server.participant import Participant


class MatchController(Controller):
    """ Leaf /match """

    def __init__(self):
        super().__init__()

        # Only allow logged-in users in a match
        self.add_access_restriction(self.check_access)
        self.set_permission_fail_handler(self.fail_permission)

        # Match creation endpoint
        self.add_endpoint(self.create_match,
                          path_restrict={"create"},
                          params_restrict={"deckupload"})
        self.add_endpoint(self.fail_permission, path_restrict={"create"})

        # Match joining endpoint
        self.add_endpoint(self.join_match, path_restrict={"join"})

        # Match leaving
        self.add_endpoint(self.abandon_match, path_restrict={"abandon"})

        self.add_endpoint(self.match)

    def check_access(self, session, path, params, headers):
        """ Checks whether the user is logged in and in a match """
        if "login" not in session:
            return False

        # Exceptions to the 'user has to be in a match rule':
        #  - Joining a match
        #  - Creating a match
        is_exempt = ("create" in path) or ("join" in path)
        if not is_exempt and Match.get_match(session["id"]) is None:
            return False

        return True

    def fail_permission(self, session, path, params, headers):
        """ Called when the user is not authorized """
        return (303,  # 303 See Other
                {"Location": "/dashboard"},
                "")

    def abandon_match(self, session, path, params, headers):
        """ Receives the request to abandon a match """
        # Leave the match
        match = Match.get_match(session["id"])
        match.abandon_participant(session["id"])

        return (303,  # 303 See Other
                {"Location": "/dashboard"},
                "")

    def join_match(self, session, path, params, headers):
        """
        Receives the request to join an existing match
        """
        if Match.get_match(session["id"]) is not None:
            # The user is already in a match
            return (303,  # 303 See Other
                    {"Location": "/match"},
                    "")

        # Get the transmitted match ID
        try:
            id = int(path[-1])
        except ValueError:
            return self.fail_permission(session, path, params, headers)

        # Get the match from the pool
        match = Match.get_by_id(id)
        if match is None or match.has_started():
            return self.fail_permission(session, path, params, headers)

        # Put the player into the match
        part = Participant(session["id"], session["nickname"])
        match.add_participant(part)

        return (303,  # 303 See Other
                {"Location": "/match"},
                "")

    def create_match(self, session, path, params, headers):
        """
        Receives the request to create a match from the form on the
        dashboard.
        """
        if Match.get_match(session["id"]) is not None:
            # The user already is in a match
            return (303,  # 303 See Other
                    {"Location": "/match"},
                    "")

        if not params["deckupload"].filename:
            # Make sure the uploaded thing is a file
            return self.fail_permission(session, path, params, headers)

        # Check the size of the upload
        fp = params["deckupload"].file
        fp.seek(0, 2)
        size = fp.tell()
        fp.seek(0)
        if size > 200 * 1024:
            return (303,  # 303 See Other
                    {"Location": "/dashboard/filesizefail"},
                    "")

        # Create a new match
        match = Match()

        # Create the deck from the upload
        match.create_deck(fp.read().decode())

        # Add the participant to the match
        part = Participant(session["id"], session["nickname"])
        match.add_participant(part)

        # Make the match available for others
        match.put_in_pool()

        return (303,  # 303 See Other
                {"Location": "/match"},
                "")

    def match(self, session, path, params, headers):
        """ The match page /match """
        # Populate symbol table
        symtab = {"theme": session["theme"]}

        # Parse the template
        data = Parser.get_template("./res/tpl/match.html", symtab)
        return (200,  # 200 OK
                {"Content-Type": "text/html; charset=utf-8"},
                data)
