"""
    Part of KgF.

    Author: LordKorea
"""

from pages.controller import Controller
from uuid import uuid4


class ResourceController(Controller):
    """
        Leaf /res
    """

    def __init__(self):
        super().__init__()
        self._etag = str(uuid4())[:6]
        self._registry = {
            "css": "text/css",
            "js": "text/javascript",
            "png": "image/png",
            "txt": "text/plain",
            "ico": "image/x-icon",
            "jpg": "image/jpeg",
        }
        self.add_endpoint(self.resource_dealer)

    def resource_dealer(self, session, path, params, headers):
        """
            Delivers resources from the resource folder
        """
        query = self._get_file_name(path)
        if query is None:
            return 404, {"Content-Type": "text/plain"}, "Not found"

        # Check if the response can be a "Not modified"
        if "if-none-match" in headers:
            if headers["if-none-match"] == self._etag:
                return (
                    304,
                    {
                        "Cache-Control": "max-age=180, public",
                        "ETag": "\"%s\"" % self._etag,
                    },
                    b"\0"
                )

        file, ext = query
        mime = self._registry.get(ext, "application/octet-stream")
        try:
            with open(file, "rb") as f:
                r = f.read()
        except OSError:
            return 404, {"Content-Type": "text/plain"}, "Not found"

        head = {
            "Content-Type": mime,
            "Cache-Control": "max-age=180, public",
            "ETag": "\"%s\"" % self._etag,
        }
        return 200, head, r

    def _get_file_name(self, path):
        """
            Fetches the file name from the path
            Returns None on failure, (filepath, extension) otherwise
        """
        if len(path) < 1:
            return None
        fn = path[0]
        if "." in fn:
            return None
        for c in fn:
            if c not in "abcdefghijklmnopqrstuvwxyz0123456789-":
                return None
        fn = fn.split("-")
        f = "./res"
        ext = "oct"
        for i in range(len(fn)):
            if i + 1 == len(fn):
                f += ".%s" % fn[i]
                ext = fn[i]
            else:
                f += "/%s" % fn[i]
        return f, ext
