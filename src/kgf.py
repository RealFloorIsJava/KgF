"""
    Part of KgF.

    Author: LordKorea
"""

from os.path import isdir
from os import mkdir
from sys import exit
from log import Log
from config import Config
import builtins


def print(str, *args, **kwargs):
    """ print() is redefined to log messages into the logger (if present) """
    if KgF.klog is None:
        builtins.print(str)
    else:
        KgF.klog.log(str)


# Exports
def kconfig():
    return KgF.kconfig


def klog():
    return KgF.klog


class KgF:
    """
        The main part of the application. Manages the web server and the
        minimal console.
    """

    klog = None
    kconfig = None

    def __init__(self):
        self._webserver = None

    def setup(self):
        # Late imports
        from web.webserver import Webserver

        print("Setting up environment...")

        # Setup data directory
        if not isdir("./data"):
            mkdir("./data", 0o0700)

        # Setup logging
        KgF.klog = Log()
        KgF.klog.setup("kgf", 4)
        print("Starting KgF...")

        # Setup configuration
        KgF.kconfig = Config()

        # Additional setup happens here!

        # Setup web server
        self._webserver = Webserver()
        if KgF.kconfig.get("dry-run", True):
            print("Dry run. Exiting...")
            exit(0)
            return
        self._webserver.start()

        # Finished setup
        print("Up and running!")

    def run(self):
        try:
            # Run console
            while True:
                builtins.print("Type quit to stop")
                inp = input("> ")
                if inp == "quit":
                    break
        finally:
            # Clean up
            builtins.print("Shutting down...")
            self._webserver.stop()
