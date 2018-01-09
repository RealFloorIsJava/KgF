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

# noinspection PyUnresolvedReferences
import readline  # noqa: Replaces default 'input' function
from os import mkdir
from os.path import isdir
from sys import exit
from typing import List, Optional, TYPE_CHECKING, Tuple

from nussschale.config import Config
from nussschale.log import Log
from nussschale.util.commands import Command


if TYPE_CHECKING:
    from nussschale.leafs.controller import Controller


class Nussschale:
    """The main class of the application. Manages the web server and console.

    Class Attributes:
        tlog: The application's logger.
        tconfig: The application's configuration.
    """

    # The logger
    nlog = None  # type: Log

    # The configuration
    nconfig = None  # type: Config

    def __init__(self) -> None:
        """Constructor."""
        # Late import to prevent circular dependencies
        from nussschale.webserver import Webserver
        from nussschale.leafs.master import MasterController
        from nussschale.leafs.resource import ResourceLeaf

        print("Setting up environment...")

        # Setup data directory
        if not isdir("./data"):
            mkdir("./data", 0o0700)  # rwx --- ---

        # Setup configuration
        Nussschale.nconfig = Config()

        # Setup logging
        Nussschale.nlog = Log()
        Nussschale.nlog.setup("nussschale", 4)
        nlog().log("Starting Nussschale...")

        # Setup web server
        self._webserver = Webserver()
        self._master = MasterController()
        self._master.add_leaf("res", ResourceLeaf)

        # Check whether the webserver should be started or whether it is just
        # an initialization run
        if Nussschale.nconfig.get("dry-run", True):
            nlog().log("Dry run. Exiting...")
            exit(0)
            return

    def start_server(self) -> None:
        """Starts the internal web server."""
        from nussschale.handler import ServerHandler

        # Set the master for the server handler
        ServerHandler.set_master(self._master)

        self._webserver.start()
        nlog().log("Up and running!")

    def add_leafs(self, leafs: List[Tuple["Controller", str]]) -> None:
        """Adds the given leafs to the server.

        Args:
            leafs: The leafs that should be added.
        """
        for controller, leaf in leafs:
            self._master.add_leaf(leaf, controller)

    def run(self) -> None:
        """Runs the minimal console."""
        try:
            print("Type `quit` to stop.")
            print("Type `help` for available commands.")

            # Run console
            while True:
                try:
                    inp = input("> ").strip()
                except (KeyboardInterrupt, EOFError):
                    # ^C, ^D
                    print()
                    break

                # Hardcoded quit command
                if inp == "quit":
                    break

                # Generic command handling
                if inp not in Command.commands:
                    print("Unknown command. Type `help` for available"
                          " commands.")
                    continue
                Command.commands[inp].invoke()
        finally:
            # Clean up
            print("Shutting down...")
            print("Please be patient while clients"
                  " are gracefully disconnected.")
            self._webserver.stop()


@Command("quit", "Stops the application.")
def quit() -> None:
    """Dummy command, just for the help entry."""
    pass


@Command("help", "Shows this help.")
def help() -> None:
    """Provides the command help."""
    print("-- Available commands")
    max_len = max([len(x) for x in Command.commands])
    for cmd in Command.commands.values():  # type: Command
        req_spaces = max_len - len(cmd.name)
        print("  %s%s - %s" % (cmd.name, " " * req_spaces, cmd.desc))


def nconfig() -> Config:
    """Provides a shortcut to fetch the application's configuration.

    Returns:
        The application's configuration.
    """
    return Nussschale.nconfig


def nlog() -> Log:
    """Provides a shortcut to fetch the application's logger.

    Returns:
        The application's logger.
    """
    return Nussschale.nlog
