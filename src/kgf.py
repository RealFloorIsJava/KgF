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

import builtins
import readline  # noqa: Replaces default 'input' function
from os import mkdir
from os.path import isdir
from sys import exit

from config import Config
from log import Log


def print(msg, *args, **kwargs):
    """Redefines print to log the message instead of printing it.

    If logging is not set up, messages will be printed via the default print()
    instead.

    Args:
        msg (str): The message to print.
        *args: Additional positional arguments are ignored but present for
            compatibility.
        **kwargs: Additional keyword arguments are ignored but present for
            compatibility.
    """
    if KgF.klog is None:
        builtins.print(msg)
    else:
        KgF.klog.log(msg)


# Exports
def kconfig():
    """Provides a shortcut to fetch the application's configuration.

    Returns:
        obj: The application's configuration.
    """
    return KgF.kconfig


def klog():
    """Provides a shortcut to fetch the application's logger.

    Returns:
        obj: The application's logger.
    """
    return KgF.klog


class KgF:
    """The main class of the application. Manages the web server and console.

    Class Attributes:
        klog (obj): The application's logger.
        kconfig (obj): The application's configuration.
    """

    # The logger
    klog = None

    # The configuration
    kconfig = None

    def __init__(self):
        """Constructor."""
        # The web server of the application
        self._webserver = None

    def setup(self):
        """Performs setup tasks and starts the integrated web server."""
        # Late imports to prevent circular dependencies when other modules
        # need configuration or logger
        from web.webserver import Webserver

        print("Setting up environment...")

        # Setup data directory
        if not isdir("./data"):
            mkdir("./data", 0o0700)  # rwx --- ---

        # Setup logging
        KgF.klog = Log()
        KgF.klog.setup("kgf", 4)
        print("Starting KgF...")

        # Setup configuration
        KgF.kconfig = Config()

        # Additional setup happens here

        # Setup web server
        self._webserver = Webserver()

        # Check whether the webserver should be started or whether it is just
        # an initialization run
        if KgF.kconfig.get("dry-run", True):
            print("Dry run. Exiting...")
            exit(0)
            return
        self._webserver.start()

        # Finished setup
        print("Up and running!")

    def run(self):
        """Runs the minimal console.

        The console only serves as means for stopping the application by using
        the command 'quit'.
        """
        # Late imports to prevent circular dependencies when other modules
        # need configuration or logger
        from model.match import Match

        stdout = builtins.print
        try:
            stdout("Type `quit` or use ^C to stop.")
            stdout("Type `help` for available commands.")

            # Run console
            while True:
                try:
                    inp = input("> ")
                except KeyboardInterrupt:
                    # ^C
                    stdout()
                    break
                except EOFError:
                    # ^D
                    stdout()
                    stdout("Type `quit` or use ^C to stop.")
                    continue

                if inp == "quit":
                    break
                elif inp == "help":
                    stdout("-- Available commands")
                    stdout("  quit     - Stops the application.")
                    stdout("  help     - Shows this help.")
                    stdout("  freeze   - Freezes all matches.")
                    stdout("  unfreeze - Unfreezes all matches.")
                elif inp == "freeze":
                    Match.frozen = True
                    stdout("Froze all matches...")
                elif inp == "unfreeze":
                    Match.frozen = False
                    stdout("Unfroze all matches...")
        finally:
            # Clean up
            stdout("Shutting down...")
            stdout("Please be patient, while clients"
                   " are gracefully disconnected.")
            self._webserver.stop()
