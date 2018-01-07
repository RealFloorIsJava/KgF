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

from functools import wraps
from json import dumps
from typing import Any, Callable, Dict, List, TYPE_CHECKING, Tuple

from nussschale.session import SessionData
from nussschale.util.types import HTTPResponse, POSTParam


if TYPE_CHECKING:
    from nussschale.leafs.controller import Controller


class EndpointContext:
    """Contains contextual information about the request.

    Attributes:
        ctrl: The controller which handles the endpoint.
        session: The session data of the client.
        path: The path of the request.
        params: The parameters of the request.
        headers: The HTTP headers of the request.
        code: The HTTP response status code.
        response_headers: The HTTP response headers.
        response: The HTTP response.
    """

    def __init__(self, ctrl: "Controller", session: SessionData,
                 path: List[str], params: Dict[str, POSTParam],
                 headers: Dict[str, str]) -> None:
        """Constructor.

        Args:
            ctrl: The controller.
            session: The client's session data.
            path: The path.
            params: The parameters of the request.
            headers: The HTTP headers.
        """
        self.ctrl = ctrl
        self.session = session
        self.path = path
        self.params = params
        self.headers = headers
        self.code = 500  # 500 Internal Server Error
        self.response_headers = {"Content-Type": "text/plain; charset=utf-8"}
        self.response = "Endpoint set no response"  # type: HTTPResponse

    def ok(self, content_type: str, response: HTTPResponse):
        """Sets the status to 200 OK.

        Args:
            content_type: Sets the content type of the response.
            response: The response.
        """
        self.code = 200  # 200 OK
        self.response_headers["Content-Type"] = content_type
        self.response = response

    def json_ok(self):
        """Sets the status to 200 OK and responds with a JSON error object."""
        self.code = 200  # 200 OK
        self.response_headers["Content-Type"] = ("application/json;"
                                                 " charset=utf-8")
        self.response = "{\"error\":\"OK\"}"


# Endpoint signatures
_Endpoint = Callable[[EndpointContext], None]
_ComplexEndpoint = Callable[
    [SessionData, List[str], Dict[str, POSTParam], Dict[str, str]],
    Tuple[int, Dict[str, str], HTTPResponse]
]

# Access Restriction signatures
_AccessRestriction = Callable[[EndpointContext], bool]
_ComplexAccessRestriction = Callable[
    [SessionData, List[str], Dict[str, POSTParam], Dict[str, str]],
    bool
]


class _HTTPExceptionGen(type):
    """Metaclass enabling HTTP exception factory methods."""

    # A list of all HTTP statuses that are injected as factory methods.
    _http_status = {
        "see_other": (303, "See Other"),
        "not_modified": (304, "Not Modified"),
        "forbidden": (403, "Forbidden"),
        "not_found": (404, "Not Found"),
        "unsupported_media_type": (415, "Unsupported Media Type")
    }

    def __getattr__(self, key: str) -> Callable[..., "HTTPException"]:
        """Injects HTTP status codes.

        Args:
            key: The attribute key.

        Returns:
            A function which creates errors for the requested kind.
        """
        assert hasattr(self, "_json")
        assert hasattr(self, "_plain")
        if key in self._http_status:
            tup = self._http_status[key]

            def create(json=False):
                if json:
                    return self._json(tup[0], {"error": tup[1]})
                else:
                    return self._plain(tup[0], tup[1])
            return create
        raise AttributeError(key)


class HTTPException(Exception, metaclass=_HTTPExceptionGen):
    """Any HTTP exception.

    Attributes:
        code: The HTTP status response code.
        headers: The response HTTP headers.
        response: The response that will be sent.
    """

    @staticmethod
    def _json(code: int, data: Any) -> "HTTPException":
        """Creates a JSON formatted HTTP exception.

        Args:
            code: The status code.
            data: The JSON object to be sent.

        Returns:
            The created HTTP exception.
        """
        return HTTPException(code, {"Content-Type": "application/json;"
                                                    " charset=utf-8"},
                             dumps(data))

    @staticmethod
    def _plain(code: int, msg: str) -> "HTTPException":
        """Creates a plaintext HTTP exception.

        Args:
            code: The status code.
            msg: The message to be sent.

        Returns:
            The created HTTP exception.
        """
        return HTTPException(code,
                             {"Content-Type": "text/plain; charset=utf-8"},
                             msg)

    def __init__(self, code: int, headers: Dict[str, str], response: str
                 ) -> None:
        """Constructor.

        Args:
            code: The HTTP status response.
            headers: The response HTTP headers.
            response: The HTTP response.
        """
        self.code = code
        self.headers = headers
        self.response = response

    def redirect(self, location: str) -> "HTTPException":
        """Sets a redirection.

        Args:
            location: Where to redirect to.

        Returns:
            The exception for chaining.
        """
        self.headers["Location"] = location
        return self

    def apply(self, ctx: EndpointContext):
        """Applies the exception to the endpoint context.

        Args:
            ctx: The endpoint context that should have the exception applied to
                it.
        """
        ctx.code = self.code
        ctx.response = self.response
        for key, value in self.headers.items():
            ctx.response_headers[key] = value


class EndpointNotApplicableException(Exception):
    """Indicates that an endpoint is not applicable in this context."""
    pass


def _wrap_access_check(ctrl: "Controller", access_chk: _AccessRestriction
                       ) -> _ComplexAccessRestriction:
    """Wraps an access check for convenience.

    Args:
        ctrl: The controller.
        access_chk: The access check that should be wrapped.

    Returns:
        The wrapped access restriction.
    """
    def complex_access_check(session: SessionData, path: List[str],
                             params: Dict[str, POSTParam],
                             headers: Dict[str, str]) -> bool:
        """A more complex access check, acting as an adapter for a simple one.

        Args:
            session: The session data of the client.
            path: The path of the request.
            params: The HTTP POST parameters.
            headers: The HTTP headers.

        Returns:
            True if access is granted, False otherwise.
        """
        ctx = EndpointContext(ctrl, session, path, params, headers)
        return access_chk(ctx)
    return complex_access_check


def _wrap_endpoint(ctrl: "Controller", endpoint: _Endpoint
                   ) -> _ComplexEndpoint:
    """Wraps an endpoint for convenience.

    Args:
        ctrl: The controller.
        endpoint: The endpoint.

    Returns:
        The wrapped endpoint.
    """
    def complex_endpoint(session: SessionData, path: List[str],
                         params: Dict[str, POSTParam], headers: Dict[str, str]
                         ) -> Tuple[int, Dict[str, str], HTTPResponse]:
        """A more complex endpoint, acting as an adapter for a simple endpoint.

        Args:
            session: The session data of the client.
            path: The path of the request.
            params: The HTTP POST parameters.
            headers: The HTTP headers.

        Returns:
            1) The HTTP response status code.
            2) The response headers to be sent.
            3) The response to be sent.
        """
        ctx = EndpointContext(ctrl, session, path, params, headers)
        try:
            endpoint(ctx)
        except HTTPException as e:
            e.apply(ctx)
        return ctx.code, ctx.response_headers, ctx.response
    return complex_endpoint


class AccessRestriction:
    """An access restriction for leafs.

    Attributes:
        ctrl: The controller this restriction belongs to.
    """

    def __init__(self, ctrl: "Controller") -> None:
        """Constructor.

        Args:
            ctrl: The controller this access restriction will be added to.
        """
        self.ctrl = ctrl

    def __call__(self, access_chk: _AccessRestriction) -> Callable[..., None]:
        """Handles decorating the restriction.

        Args:
            access_chk: The access restriction which should be decorated.

        Return:
            A function which should not be called.
        """
        self.ctrl.add_access_restriction(_wrap_access_check(self.ctrl,
                                                            access_chk))

        @wraps(access_chk)
        def disabled_function(*_, **__):
            """A function which may not be called.

            Args:
                *_: Ignored.
                **__: Ignored.

            Raises:
                TypeError: always.
            """
            raise TypeError("can't call access check directly!")
        return disabled_function


class Endpoint:
    """An endpoint that catches everything.

    Attributes:
        ctrl: The controller this endpoint belongs to.
    """

    def __init__(self, ctrl: "Controller") -> None:
        """Constructor.

        Args:
            ctrl: The controller for the endpoint.
        """
        self.ctrl = ctrl

    def __call__(self, endpoint: _Endpoint) -> _Endpoint:
        """Handles decorating the endpoint.

        Args:
            endpoint: The endpoint to be decorated.

        Returns:
            The endpoint itself. Should not be decorated any more.
        """
        self.ctrl.add_endpoint(_wrap_endpoint(self.ctrl, endpoint))
        return endpoint


class RequirePath:
    """Modifies an endpoint to make it require certain elements in the path.

    Attributes:
        path: The path elements that are required.
    """

    def __init__(self, *args) -> None:
        """Constructor.

        Args:
            *args: Strings which have to be in the path.
        """
        assert len(args) > 0
        assert all(isinstance(x, str) for x in args)
        self.path = list(args)  # type: List[str]

    def __call__(self, endpoint: _Endpoint) -> _Endpoint:
        """Modifies the endpoint to require path elements.

        Args:
            endpoint: The endpoint to be decorated.

        Returns:
            The modified endpoint.
        """
        @wraps(endpoint)
        def wrapper(ctx: EndpointContext):
            """Checks whether all required path elements are present.

            Args:
                ctx: The context of the request.

            Raises:
                EndpointNotApplicableException: When path elements are not
                    present.
            """
            for elem in self.path:
                if elem not in ctx.path:
                    raise EndpointNotApplicableException()
            endpoint(ctx)
        return wrapper


class OnlyIf:
    """Modifies an endpoint to be disabled, depending on a parameter.

    Attributes:
        enabled: True if the endpoint is enabled.
    """

    def __init__(self, enabled: bool) -> None:
        """Constructor.

        Args:
            enabled: Whether the endpoint is enabled.
        """
        self.enabled = enabled

    def __call__(self, endpoint: _Endpoint) -> _Endpoint:
        """Modifies an endpoint to be possibly disabled.

        Args:
            endpoint: The endpoint to be decorated.

        Returns:
            The modified endpoint.
        """
        @wraps(endpoint)
        def wrapper(ctx: EndpointContext):
            """Potentially disables an endpoint.

            Args:
                ctx: The context of the request.

            Raises:
                EndpointNotApplicableException: When disabled.
            """
            if not self.enabled:
                raise EndpointNotApplicableException()
            endpoint(ctx)
        return wrapper


class RequireParameters:
    """Modifies an endpoint to make it require certain HTTP POST parameters.

    Attributes:
        params: The parameters that are required.
    """

    def __init__(self, *args) -> None:
        """Constructor.

        Args:
            *args: Strings which have to be in the parameters.
        """
        assert len(args) > 0
        assert all(isinstance(x, str) for x in args)
        self.params = list(args)  # type: List[str]

    def __call__(self, endpoint: _Endpoint) -> _Endpoint:
        """Modifies an endpoint to require parameters.

        Args:
            endpoint: The endpoint to be decorated.

        Returns:
            The modified endpoint.
        """
        @wraps(endpoint)
        def wrapper(ctx: EndpointContext):
            """Checks whether all required parameters are present.

            Args:
                ctx: The context of the request.

            Raises:
                EndpointNotApplicableException: When parameters are not
                    present.
            """
            for param in self.params:
                if param not in ctx.params:
                    raise EndpointNotApplicableException()
            endpoint(ctx)
        return wrapper


class PermissionFailHandler:
    """An endpoint called when access checks fail.

    Attributes:
        ctrl: The controller this endpoint belongs to.
    """

    def __init__(self, ctrl: "Controller") -> None:
        """Constructor.

        Args:
            ctrl: The controller for the handler.
        """
        self.ctrl = ctrl

    def __call__(self, handler: _Endpoint) -> _Endpoint:
        """Handles decorating the handler.

        Args:
            handler: The permission handler to be decorated

        Returns:
            The handler itself. Should not be decorated any more.
        """
        self.ctrl.set_permission_fail_handler(_wrap_endpoint(self.ctrl,
                                                             handler))
        return handler
