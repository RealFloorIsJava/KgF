"""
    Part of KgF.

    Author: LordKorea
"""

from os.path import exists
from json import dump, load
from threading import RLock


class Config:
    _CONFIG_FILE = "./data/kgf.json"

    def __init__(self):
        self._lock = RLock()
        self._configuration = {}

        # Create file, if not exists
        if not exists(Config._CONFIG_FILE):
            with open(Config._CONFIG_FILE, "w") as f:
                dump(self._configuration, f, indent=4, sort_keys=True)

        # Get configuration
        with open(Config._CONFIG_FILE, "r") as f:
            self._configuration = load(f)

    def get(self, key, default):
        with self._lock:
            # Set the default and write-back
            if key not in self._configuration:
                self._configuration[key] = default
                with open(Config._CONFIG_FILE, "w") as f:
                    dump(self._configuration, f, indent=4, sort_keys=True)

            return self._configuration[key]
