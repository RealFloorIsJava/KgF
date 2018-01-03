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

Module Deadlock Guarantees:
    When the mutex of the configuration is locked no other locks can be
    requested. Thus the configuartion lock can not be part of any deadlock.
"""

from json import dump, load
from os.path import exists
from threading import RLock

from util.locks import mutex


class Config:
    """Manages the JSON configuration file."""

    # The configuration file where keys and values will be stored
    _CONFIG_FILE = "./data/kgf.json"

    def __init__(self):
        """Constructor."""
        # MutEx for configuration access.
        # Locking this MutEx can't cause any other MutExes to be locked.
        self._lock = RLock()
        # The configuration cache which keeps the configuration in memory
        self._configuration = {}

        # Create file, if not exists
        if not exists(Config._CONFIG_FILE):
            with open(Config._CONFIG_FILE, "w") as f:
                dump(self._configuration, f, indent=4, sort_keys=True)

        # Get configuration
        with open(Config._CONFIG_FILE, "r") as f:
            self._configuration = load(f)

    @mutex
    def get(self, key, default):
        """Gets the value for the given configuration key.

        If the configuration key has no associated value then a default value
        will be set.

        Args:
            key (str): The configuration key.
            default (any): The default value for the configuration key.

        Contract:
            This method locks the configuration lock.
        """
        # Set the default and write-back
        if key not in self._configuration:
            self._configuration[key] = default
            with open(Config._CONFIG_FILE, "w") as f:
                dump(self._configuration, f, indent=4, sort_keys=True)

        return self._configuration[key]
