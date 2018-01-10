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

from typing import List, Optional, Tuple
from uuid import uuid4

from nussschale.leafs.controller import Controller
from nussschale.leafs.endpoint import Endpoint, EndpointContext, HTTPException


def _get_file_name(path: List[str]) -> Optional[Tuple[str, str]]:
    """Fetches the file name from the path.

    Args:
        path: The list of elements in the path

    Returns:
        None is returned on failure. If the path contains
        a valid file path the tuple will contain the path in the first
        element. The second element will be the extension of the file.
    """
    # The path may not be empty
    if len(path) < 1:
        return None

    # Check that the path is sanitized
    # Path elements may only contain alphabetic characters, numbers and
    # dashes. Only the last path element may have exactly one dot.
    for i in range(len(path)):
        is_last = i == len(path) - 1
        has_dot = False
        has_chars = False
        for c in path[i]:
            if c == ".":
                if not is_last:
                    return None  # dots not in last element
                if has_dot:
                    return None  # multiple dots
                if not has_chars:
                    return None  # element starts with a dot
                has_dot = True
            elif c not in ("abcdefghijklmnopqrstuvwxyz"
                           "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                           "0123456789-"):
                return None  # illegal character
            has_chars = True

    # Construct the file name
    fn = "/".join(path)
    if "." not in fn:
        return None  # no file extension
    dot_idx = fn.index(".")

    f = "./res/%s" % fn
    ext = fn[(dot_idx + 1):]
    return f, ext


class ResourceController(Controller):
    """Handles the /res leaf.

    Class Attributes:
        max_cache: The TTL for cache items that will be sent.
        etag: The E-Tag that will be sent for resource requests.
        registry: A mapping of file extensions to media types.
    """

    # The maximum number of seconds for which a resource is cached.
    max_cache = 3 * 60  # 3 minutes

    # Use the same ETag for all requests. Because the ETag is regenerated
    # when the application is restarted, cache is only kept for as long
    # as the application is running (which should be fine in production
    # scenarios)
    etag = str(uuid4())[:6]  # 16^6 possible etags, little chance for problems

    # Content type registry for common files
    registry = {"css": "text/css; charset=utf-8",
                "js": "text/javascript; charset=utf-8",
                "png": "image/png",
                "txt": "text/plain; charset=utf-8",
                "ico": "image/x-icon",
                "jpg": "image/jpeg",
                "svg": "image/svg+xml"}


ResourceLeaf = ResourceController()


@Endpoint(ResourceLeaf)
def resource_dealer(ctx: EndpointContext) -> None:
    """Delivers resources from the resource folder.

    Args:
        ctx: The context of the request.

    Raises:
        HTTPException: (403) For invalid file names.
                       (304) When the resource is cached by the client.
                       (404) When a resource file does not exist.
    """
    cache_ctrl = "max-age=%i, public" % ResourceController.max_cache
    wrapped_etag = "\"%s\"" % ResourceController.etag

    # Reads the filename from the path
    query = _get_file_name(ctx.path)
    if query is None:
        raise HTTPException.forbidden()

    # Check if the response can be a "Not modified"
    if "if-none-match" in ctx.headers:
        if ctx.headers["if-none-match"] == wrapped_etag:
            ctx.response_headers["Cache-Control"] = cache_ctrl
            ctx.response_headers["ETag"] = wrapped_etag
            raise HTTPException.not_modified()

    # Load the requested resource file.
    # Permission and sanity checks have already been performed statically
    # when parsing the query
    file, ext = query
    mime = ResourceController.registry.get(ext, "application/octet-stream")
    try:
        with open(file, "rb") as f:
            r = f.read()
    except OSError:
        raise HTTPException.not_found()

    ctx.response_headers["Cache-Control"] = cache_ctrl
    ctx.response_headers["ETag"] = wrapped_etag
    ctx.ok(mime, r)
