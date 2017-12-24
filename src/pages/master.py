"""
    Part of KgF.

    Author: LordKorea
"""

from pages.controller import Controller


class MasterController(Controller):
    """
        Dispatches request to the respective controllers
        which can also be registered here
    """

    _LEAF_INJECT = "___leaf___"

    def __init__(self):
        super().__init__()

    def decorate_params(self, leaf, params):
        """
            Adds the magic leaf parameter to the given parameters
        """
        magic = "%s:%s" % (MasterController._LEAF_INJECT, leaf)
        params[magic] = True

    def add_leaf(self, leaf, ctrl):
        """
            Adds a top level leaf to the master controller. This should
            be a controller by itself.
        """
        # Restrict for magic leaf parameter
        magic = "%s:%s" % (MasterController._LEAF_INJECT, leaf)

        # Add the decorated endpoint
        self.add_endpoint(
            self.decorate_endpoint_call(ctrl.call_endpoint, magic),
            params_restrict={magic}
        )

    def decorate_endpoint_call(self, call, magic):
        """
            Wraps an endpoint call to remove the magic leaf parameter
        """
        def _decorated_call(session, path, params, headers):
            if magic in params:
                del params[magic]
            return call(session, path, params, headers)
        _decorated_call.__doc__ = call.__doc__
        _decorated_call.__name__ = call.__name__
        return _decorated_call
