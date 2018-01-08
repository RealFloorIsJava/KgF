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
from nussschale.util.heartbeat import Heartbeat


@Heartbeat
def housekeeping() -> None:
    """Called for every request."""
    Match.perform_housekeeping()


@Command("freeze", "Freezes all match timers.")
def freeze() -> None:
    """Freezes all matches."""
    Match.frozen = True
    print("All matchs are now frozen.")


@Command("unfreeze", "Unfreezes all match timers.")
def unfreeze() -> None:
    """Unfreezes all matches."""
    Match.frozen = False
    print("All matches are no longer frozen.")


# Entry point
if __name__ == "__main__":
    ns = Nussschale()

    from pages.api import APILeaf
    from pages.dashboard import DashboardLeaf
    from pages.deckedit import DeckeditLeaf
    from pages.index import IndexLeaf
    from pages.match import MatchLeaf
    from pages.options import OptionsLeaf

    ns.add_leafs([
        (APILeaf, "api"),
        (DashboardLeaf, "dashboard"),
        (DeckeditLeaf, "deckedit"),
        (IndexLeaf, "index"),
        (MatchLeaf, "match"),
        (OptionsLeaf, "options")
    ])

    ns.start_server()
    ns.run()
