"""
Part of KgF.

Author: LordKorea
"""

from logging import ERROR, FileHandler, Formatter, INFO, getLogger
from os import mkdir, remove, rename
from os.path import isfile
from threading import RLock


class Log:
    """ Provides logging utilities """
    def __init__(self):
        # MutEx to enable multiple connections logging at the same time
        # Locking this MutEx can't cause any other MutExes to be locked.
        self._lock = RLock()
        # The logger itself
        self._logger = None
        # The number of logs that are kept
        self._storage = 3

    def setup(self, name, storage):
        """ Setup the logger with the given name and log roll setting """
        self._logger = getLogger("%s_log" % name)
        self._storage = storage

        # Create the log directory
        try:
            mkdir("./logs")
        except OSError:
            pass  # Already exists

        # Setup the logger itself
        formatter = Formatter("[%(asctime)s %(levelname)s] %(message)s")
        handler = FileHandler(self._log_roll(name, self._storage))
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(INFO)

    def log(self, msg):
        """ Log a message (informational) """
        with self._lock:
            self._logger.log(msg=msg, level=INFO)

    def error(self, msg):
        """ Log a message (error) """
        with self._lock:
            self._logger.log(msg=msg, level=ERROR)

    def _log_roll(self, keyword, storage=5):
        """ Roll the log files """
        storage -= 1

        # Set the format for logger filenames
        fmt = "./logs/" + keyword + ".%i.log"

        # Remove the last logfile if it exists
        if isfile(fmt % storage):
            remove(fmt % storage)

        # Change the name of every log file so that the first id is no longer
        # taken
        for i in range(storage)[::-1]:
            if isfile(fmt % i):
                rename(fmt % i, fmt % (i + 1))

        # Return the final file name, with ID 0 (this name is now free)
        return fmt % 0
