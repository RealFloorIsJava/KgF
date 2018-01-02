"""Part of KgF.

MIT License
Copyright (c) 2017 LordKorea

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

from uuid import uuid4

from pages.controller import Controller


class ResourceController(Controller):
    """Handles the /res leaf."""

    # The maximum number of seconds for which a resource is cached.
    _MAX_CACHE = 60 * 60 * 24 * 180  # 1/2 year

    def __init__(self):
        """Constructor."""
        super().__init__()
        # Use the same ETag for all requests. Because the ETag is regenerated
        # when the application is restarted, cache is only kept for as long
        # as the application is running (which should be fine in production
        # scenarios)
        self._etag = str(uuid4())[:6]
        # Content type registry for common files
        self._registry = {"css": "text/css",
                          "js": "text/javascript",
                          "png": "image/png",
                          "txt": "text/plain",
                          "ico": "image/x-icon",
                          "jpg": "image/jpeg",
                          "svg": "image/svg+xml"}

        # Register the resource delivery endpoint
        self.add_endpoint(self.resource_dealer)

    def resource_dealer(self, session, path, params, headers):
        """Delivers resources from the resource folder.

        Args:
            session (obj): The session data of the client.
            path (list): A list containg all elements in the request path.
            params (dict): A dictionary of all POST parameters.
            headers (dict): A dictionary of all HTTP headers.

        Returns:
            tuple: Returns 1) the HTTP status code 2) the HTTP headers to be
                sent and 3) the response to be sent to the client.
        """
        # Reads the file name from the path
        query = self._get_file_name(path)
        if query is None:
            # 403 Forbidden
            return 403, {"Content-Type": "text/plain"}, "Forbidden"

        # Check if the response can be a "Not Modified"
        if "if-none-match" in headers:
            if headers["if-none-match"] == "\"%s\"" % self._etag:
                return (304,  # 304 Not Modified
                        {"Cache-Control": "max-age=%i, public"
                         % ResourceController._MAX_CACHE,
                         "ETag": "\"%s\"" % self._etag},
                        b"\0")

        # Load the requested resource file.
        # Permission and sanity checks have already been performed statically
        # when parsing the query
        file, ext = query
        mime = self._registry.get(ext, "application/octet-stream")
        try:
            with open(file, "rb") as f:
                r = f.read()
        except OSError:
            # 404 Not Found
            return 404, {"Content-Type": "text/plain"}, "Not found"

        head = {"Content-Type": mime,
                "Cache-Control": "max-age=%i, public"
                % ResourceController._MAX_CACHE,
                "ETag": "\"%s\"" % self._etag}
        # 200 OK
        return 200, head, r

    def _get_file_name(self, path):
        """Fetches the file name from the path.

        Args:
            path (list): The list of elements in the path

        Returns:
            tuple or None: None is returned on failure. If the path contains
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
