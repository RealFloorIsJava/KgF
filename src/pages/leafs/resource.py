"""
Part of KgF.

Author: LordKorea
"""


from uuid import uuid4

from pages.controller import Controller


class ResourceController(Controller):
    """ Leaf /res """

    # The number of seconds for which a resource is cached
    _MAX_CACHE = 180

    def __init__(self):
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
        """ Delivers resources from the resource folder """
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
        """
        Fetches the file name from the path
        Returns None on failure, (filepath, extension) otherwise
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
