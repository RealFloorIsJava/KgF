"""
    Part of KgF.

    Author: LordKorea
"""

from threading import RLock
from logging import getLogger, FileHandler, Formatter, INFO, ERROR
from os import mkdir, remove, rename
from os.path import isfile


class Log:
    """ Provides logging utilities """
    def __init__(self):
        self._lock = RLock()
        self._logger = None
        self._storage = 3

    def setup(self, name, storage):
        """ Setup the logger with the given name and log roll setting """
        self._logger = getLogger("%s_log" % name)
        self._storage = storage

        try:
            mkdir("./logs")
        except OSError:
            pass  # Already exists

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
        fmt = "./logs/" + keyword + ".%i.log"
        if isfile(fmt % storage):
            remove(fmt % storage)
        for i in range(storage)[::-1]:
            if isfile(fmt % i):
                rename(fmt % i, fmt % (i + 1))
        return fmt % 0
