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
    _MAX_CACHE = 180

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
            # 404 Not Found
            return 404, {"Content-Type": "text/plain"}, "Not found"

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

        The first element of the path is split by dashes into a list of tokens.
        The last two tokens will be used for the filename (filename +
        extension). The other tokens will be translated into directories.

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
        # The file may only contain [a-z][0-9] and the dash (-)
        fn = path[0]
        for c in fn:
            if c not in "abcdefghijklmnopqrstuvwxyz0123456789-":
                return None

        fn = fn.split("-")
        f = "./res"
        ext = "oct"

        # Construct the file from the dash seperated name
        # The last element is the extension, all others are path elements
        for i in range(len(fn)):
            if i + 1 == len(fn):
                f += ".%s" % fn[i]
                ext = fn[i]
            else:
                f += "/%s" % fn[i]
        return f, ext
