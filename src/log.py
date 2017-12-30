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

Module Deadlock Guarantees:
    When the logger's mutex is locked no other locks can be requested.
    Thus the logger's mutex can not be part of any deadlock.
"""

from logging import ERROR, FileHandler, Formatter, INFO, getLogger
from os import mkdir, remove, rename
from os.path import isfile
from threading import RLock

from util.locks import mutex


class Log:
    """Provides logging utilities and log rotation."""

    def __init__(self):
        """Constructor."""
        # MutEx to enable multiple connections logging at the same time
        # Locking this MutEx can't cause any other MutExes to be locked.
        self._lock = RLock()
        # The logger itself
        self._logger = None
        # The number of logs that are kept
        self._storage = 3

    def setup(self, name, storage):
        """Setup the logger with the given name and log roll setting.

        Args:
            name (str): The name of the log file.
            storage (int): The number of log files that should be kept in the
                log directory.
        """
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

    @mutex
    def log(self, msg):
        """Logs a non-critical message.

        Args:
            msg (str): The message that should be logged.

        Contract:
            This method locks the logger's lock.
        """
        self._logger.log(msg=msg, level=INFO)

    @mutex
    def error(self, msg):
        """Logs a message that describes an error or a critical condition.

        Args:
            msg (str): The message that should be logged.

        Contract:
            This method locks the logger's lock.
        """
        self._logger.log(msg=msg, level=ERROR)

    def _log_roll(self, keyword, storage=5):
        """Deletes and renames old log files and finds a new log file name.

        Args:
            keyword (str): The name of the log file.
            storage (int, optional): How many log files should be kept. The
                default is 5.

        Returns:
            str: A file name that can be used for the next log file.
        """
        # Set the format for logger filenames
        fmt = "./logs/%s.%%i.log" % keyword

        # Change the name of every log file so that the first id is no longer
        # taken
        for i in range(storage)[::-1]:
            if isfile(fmt % i):
                rename(fmt % i, fmt % (i + 1))

        # Remove the last logfile if it exists
        if isfile(fmt % storage):
            remove(fmt % storage)

        # Return the final file name, with ID 0 (this name is now free)
        return fmt % 0
