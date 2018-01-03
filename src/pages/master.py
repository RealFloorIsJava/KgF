"""Part of KgF.

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

from pages.controller import Controller


class MasterController(Controller):
    """Dispatches requests to the respective leaf controllers."""

    # The key for the parameter that will be injected
    _LEAF_INJECT = "___leaf___"

    def decorate_params(self, leaf, params):
        """Includes the leaf parameter in the POST parameters.

        The parameter is constructed in a way to make name collisions less
        likely.

        Args:
            leaf (str): The leaf that will be selected.
            params (dict): The dictionary of POST parameters.
        """
        magic = "%s:%s" % (MasterController._LEAF_INJECT, leaf)
        params[magic] = True

    def add_leaf(self, leaf, ctrl):
        """Adds a leaf controller to the master controller.

        Args:
            leaf (str): The leaf which should be handled by the controller.
            ctrl (obj): The controller which will handle requests for the leaf.
        """
        # Restriction for the magic leaf parameter
        magic = "%s:%s" % (MasterController._LEAF_INJECT, leaf)

        # Add the decorated endpoint
        self.add_endpoint(
            self.decorate_endpoint_call(ctrl.call_endpoint, magic),
            params_restrict={magic})

    def decorate_endpoint_call(self, call, magic):
        """Wraps an endpoint call to remove the magic leaf parameter.

        Args:
            call (function): The endpoint call that should be wrapped.
            magic (str): The parameter name that should be removed.

        Returns:
            function: The wrapped endpoint call.
        """
        def _decorated_call(session, path, params, headers):
            if magic in params:
                del params[magic]
            return call(session, path, params, headers)
        _decorated_call.__doc__ = call.__doc__
        _decorated_call.__name__ = call.__name__
        return _decorated_call
