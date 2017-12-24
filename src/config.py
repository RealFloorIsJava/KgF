"""
Part of KgF.

Author: LordKorea
"""

from json import dump, load
from os.path import exists
from threading import RLock


class Config:
    """ Manages the JSON configuration file """

    # The configuration file where keys and values will be stored
    _CONFIG_FILE = "./data/kgf.json"

    def __init__(self):
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

    def get(self, key, default):
        """
        Fetches the value for the given key or sets the value to the given
        default
        """
        with self._lock:
            # Set the default and write-back
            if key not in self._configuration:
                self._configuration[key] = default
                with open(Config._CONFIG_FILE, "w") as f:
                    dump(self._configuration, f, indent=4, sort_keys=True)

            return self._configuration[key]
