"""
Part of KgF.

Author: LordKorea
"""


class Controller:
    """
    Represents a page controller, managing access restrictions and
    endpoints
    """

    def __init__(self):
        # Access restrictions
        self._restrictions = []
        # Endpoints
        self._endpoints = []
        # The default access denied handler
        self._access_denied = lambda x, y, z, h: (
            403,  # 403 Forbidden
            {"Content-Type": "text/plain"},
            "Access denied")

    def add_access_restriction(self, chk):
        """
        Adds an access restriction for this controller.
        The restriction is a function
            (session_data, path, params, headers) -> (bool)
        with True for access granted, False for access denied
        Access is denied iff a denying restriction exists.
        """
        self._restrictions.append(chk)

    def set_permission_fail_handler(self, point):
        """
        This will be called as an endpoint if access checks fail.
        For signature, see add_endpoint()
        """
        self._access_denied = point

    def add_endpoint(self, point, path_restrict=None, params_restrict=None):
        """
        Adds an endpoint for this controller.
        For "point" to be called, path_restrict must be present in the
        path and params_restrict must be existing keys in the parameters.
        The endpoint has to return an integer (http status code),
        a dictionary (http headers) and a string (http response):

        (session, path, params, headers) -> (status, headers, response)
        """
        # Default path restriction is no restriction
        if path_restrict is None:
            path_restrict = set()

        # Default parameter restriction is no restriction
        if params_restrict is None:
            params_restrict = set()

        # Structure: [(path,param) -> (endpoint)]
        self._endpoints.append(((path_restrict, params_restrict), point))

    def call_endpoint(self, session_data, path, params, headers):
        """
        Calls an endpoint and returns the results.
        """
        # Access check
        passed = True
        for check in self._restrictions:
            if not check(session_data, path, params, headers):
                passed = False
                break

        # Access denied check
        if not passed:
            return self._access_denied(session_data, path, params, headers)

        # Find endpoint
        for point in self._endpoints:
            path_restrict = point[0][0]
            params_restrict = point[0][1]
            callback = point[1]
            fail = False

            # Check path
            for request in path_restrict:
                if request not in path:
                    fail = True
                    break

            # Early bailout
            if fail:
                continue

            # Check params
            for request in params_restrict:
                if request not in params:
                    fail = True
                    break

            # Late bail out
            if fail:
                continue

            # Endpoint matches, call endpoint callback
            res = callback(session_data, path, params, headers)
            if res is None:
                # Fall through, the next endpoint should be considered
                continue
            return res

        # Last resort if there is no matching endpoint
        return (404,  # 404 Not Found
                {"Content-Type": "text/plain"},
                "No applicable endpoint found")
