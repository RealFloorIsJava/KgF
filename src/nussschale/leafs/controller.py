"""Part of Nussschale.

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

from typing import Callable, Dict, List, Tuple

from nussschale.leafs.endpoint import EndpointNotApplicableException
from nussschale.session import SessionData
from nussschale.util.types import Endpoint, HTTPResponse, POSTParam


# A restriction function for access to leafs
AccessRestriction = Callable[
    ["SessionData", List[str], Dict[str, POSTParam], Dict[str, str]],
    bool
]


def default_access_denied(session: SessionData, path: List[str],
                          params: Dict[str, POSTParam], headers: Dict[str, str]
                          ) -> Tuple[int, Dict[str, str], HTTPResponse]:
    """The default access denied handler.

    Args:
        session: The session data of the client.
        path: The path of the request.
        params: The HTTP POST parameters.
        headers: The HTTP headers that were sent by the client.

    Returns:
        Returns 1) the HTTP status code 2) the HTTP headers to be
        sent and 3) the response to be sent to the client.
    """
    return (403,  # 403 Forbidden
            {"Content-Type": "text/plain; charset=utf-8"},
            "Access denied")


class Controller:
    """A base page controller, managing access restrictions and endpoints."""

    def __init__(self):
        """Constructor."""
        # Access restrictions
        self._restrictions = []  # type: List[AccessRestriction]
        # Endpoints
        self._endpoints = []  # type: List[Endpoint]
        # The default access denied handler
        self._access_denied = default_access_denied

    def add_access_restriction(self, chk: AccessRestriction):
        """Adds an access restriction for this controller.

        The restriction is a function
            (session, path, params, headers) -> (bool)
        The function should return True if and only if access is granted.
        If at least one of the added access restrictions returns False, access
        is denied.
        Restrictions will be checked before any endpoint is called.

        Args:
            chk: The restriction as described above.
        """
        self._restrictions.append(chk)

    def set_permission_fail_handler(self, point: Endpoint):
        """Sets the handler for when access is denied.

        This will be called as an endpoint if any access check fails.
        The signature of the function is
            (session, path, params, headers) -> (status, headers, response)
        See add_endpoint() for a more detailed description of the signature.

        Args:
            point: The handler as described above.
        """
        self._access_denied = point

    def add_endpoint(self, point: Endpoint):
        """Adds an endpoint to this controller.

        The given callback function will be called if and only if the following
        conditions hold:
            - The access checks must not fail.
            - Any other endpoint that was added before this endpoint is not
                called or raises an EndpointNotApplicableException.

        The callback function has the following signature:
            (session, path, params, headers) -> (status, headers, response)
        session is a SessionData object containing the user's session data.
        path is a list of elements in the path.
        params is a dictionary of POST parameters.
        headers is a dictionary of HTTP headers.
        status is the HTTP status code that should be sent in response to the
            request.
        headers is a dictionary of HTTP headers that should be sent in
            response to the request.
        response is a string that will be sent as the body of the response.

        Args:
            point: The endpoint callback function as described
                above.
        """
        self._endpoints.append(point)

    def call_endpoint(self, session_data: SessionData, path: List[str],
                      params: Dict[str, POSTParam], headers: Dict[str, str]
                      ) -> Tuple[int, Dict[str, str], HTTPResponse]:
        """Calls an endpoint and returns the results.

        For details on which endpoint(s) will be called, check the
        documentation of add_endpoint or set_permission_fail_handler.

        Args:
            session_data: The session data of the client.
            path: The path of the request.
            params: The POST parameters of the request.
            headers: The HTTP headers of the request.

        Returns:
            Returns 1) the HTTP status code 2) the HTTP headers to be
            sent and 3) the response to be sent to the client.
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
            try:
                return point(session_data, path, params, headers)
            except EndpointNotApplicableException:
                pass  # Check next endpoint

        # Last resort if there is no matching endpoint
        return (500,  # 500 Internal Server Error
                {"Content-Type": "text/plain; charset=utf-8"},
                "No applicable endpoint found")
