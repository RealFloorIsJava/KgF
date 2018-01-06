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

from model.match import Match
from nussschale.nussschale import Nussschale
from nussschale.util.commands import Command
from pages.api import APIController
from pages.dashboard import DashboardController
from pages.deckedit import DeckeditController
from pages.index import IndexController
from pages.match import MatchController
from pages.options import OptionsController


def request_listener():  # TODO
    """Called for every request."""
    Match.perform_housekeeping()


@Command("freeze", "Freezes all match timers.")
def freeze():
    """Freezes all matches."""
    Match.frozen = True
    print("All matchs are now frozen.")


@Command("unfreeze", "Unfreezes all match timers.")
def unfreeze():
    """Unfreezes all matches."""
    Match.frozen = False
    print("All matches are no longer frozen.")


# Entry point
if __name__ == "__main__":
    ns = Nussschale()

    ns.add_request_listener(request_listener)
    ns.add_leafs([
        (APIController, "api"),
        (DashboardController, "dashboard"),
        (DeckeditController, "deckedit"),
        (IndexController, "index"),
        (MatchController, "match"),
        (OptionsController, "options")
    ])

    ns.start_server()
    ns.run()
