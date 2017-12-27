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
    The following lock dependencies are introduced by this module:
        Session Pool Lock -> Session Instance Lock
        Session Instance Lock -> Configuration Lock

    The session data mutex allows no other locks to be requested and therefor
    can not be part of any deadlock.
"""

from threading import RLock
from time import time
from uuid import uuid4

from kgf import kconfig


class Session:
    """Represents a client session whic is kept open by a session cookie."""

    # The MutEx for the session pool
    # Locking this MutEx can cause the Session MutEx to be locked.
    _pool_lock = RLock()

    # The session pool, all currently existing sessions, sid->session
    _sessions = {}

    @staticmethod
    def get_session(ip, sid=None):
        """Retrieves an existing session or creates a new one.

        A new session is created for the user if and only if at least one of
        the following conditions holds:
            - sid is None
            - sid is not in the session pool
            - a session is found but it is expired
            - a session is found but the IP addresses do not match

        Args:
            ip (str): The IP address of the user making the request.
            sid (str): The session ID provided by the user or None if none was
                provided.

        Returns:
            (obj, bool): The session of the user and whether it was newly
                created.

        Contract:
            This method will lock
                - the session pool's lock
                - the session's instance lock
            in the aforementioned order and may possess both locks at the same
            time.
        """
        # Create new session if it was explicitly requested
        if sid is None:
            return Session(ip), True

        with Session._pool_lock:
            # Unknown SID -> new session
            if sid not in Session._sessions:
                return Session(ip), True

            # Fetch (maybe invalid) session
            session = Session._sessions[sid]
            create = False

            # A session expires when it was not used for some time or the
            # IP of the owner changes (basic hijacking protection)
            if session.is_expired() or not session.is_owner(ip):
                # Delete the old session and create a new one
                del Session._sessions[sid]
                session = Session(ip)
                create = True
            return session, create

    def __init__(self, ip):
        """Constructor.

        Args:
            ip (str): The IP address of the owner of the session.

        Contract:
            This method locks the session pool's lock.
        """
        # The MutEx for an individual session
        # Locking this MutEx can't cause any other MutExes to be locked.
        self._lock = RLock()

        # Generate a random session ID and store the session owner's IP
        self._sid = str(uuid4())
        self._ip = ip

        # Expires X minutes into the future
        self._expires = 0
        self.refresh()

        # Initialize session data
        self._data = SessionData()

        # Insert this session into the pool
        with Session._pool_lock:
            Session._sessions[self._sid] = self

    def is_expired(self):
        """Checks whether this session is past its expiration date.

        Returns:
            bool: Whether the session is no longer valid due to expiration.

        Contract:
            This method will lock the session's instance lock.
        """
        with self._lock:
            return self._expires <= time()

    def is_owner(self, ip):
        """Checks whether the given IP is the owner of this session.

        Returns:
            bool: True if the owner has the same IP, False otherwise.

        Contract:
            This method will lock the session's instance lock.
        """
        with self._lock:
            return self._ip == ip

    def refresh(self):
        """Refreshes the session by resetting the expiration timer.

        Contract:
            This method will lock the session's instance lock and the
            configuration lock in that order.
        """
        with self._lock:
            expire_time = kconfig().get("expire_time", 15)
            self._expires = time() + expire_time * 60

    def get_id(self):
        """Returns the session ID.

        Returns:
            str: The session ID.

        Contract:
            This method will lock the session's instance lock.
        """
        with self._lock:
            return self._sid

    def get_data(self):
        """Returns the session's data.

        Returns:
            obj: The SessionData object associated with the session.

        Contract:
            This method will lock the session's instance lock.
        """
        with self._lock:
            return self._data


class SessionData:
    """Represents session data as a thread-safe dictionary."""

    def __init__(self):
        """Constructor."""
        # The MutEx for the session data
        # Locking this MutEx can't cause any other MutExes to be locked.
        self._lock = RLock()

        # The internals of the session data
        self._internal = {}

    def remove(self, key):
        """Removes the entry with the given key from the session data.

        Args:
            key (any): A suitable dictionary key for the entry.

        Contract:
            This method will lock the session's data lock.
        """
        with self._lock:
            del self._internal[key]

    def get(self, key, default=None):
        """Retrieves the entry with the given key or the given default value.

        Args:
            key (any): The key of the entry.
            default (any, optional): The default value when the key is not
                found.

        Returns:
            any: The entry for the given key (or the default value).

        Contract:
            This method will lock the session's data lock.
        """
        with self._lock:
            return self._internal.get(key, default)

    def __len__(self):
        """Retrieves the length of the data dictionary.

        Returns:
            int: The number of entries in the dictionary

        Contract:
            This method will lock the session's data lock.
        """
        with self._lock:
            return len(self._internal)

    def __getitem__(self, key):
        """Retrieves the entry for the given key.

        Args:
            key (any): The key of the entry to retrieve.

        Returns:
            any: The entry associated with the given key.

        Contract:
            This method will lock the session's data lock.
        """
        with self._lock:
            return self._internal[key]

    def __setitem__(self, key, value):
        """Sets the entry for the given key in the session data.

        Args:
            key (any): The key which will be used for storing the entry.
            value (any): The entry to store associated with the given key.

        Contract:
            This method will lock the session's data lock.
        """
        with self._lock:
            self._internal[key] = value

    def __contains__(self, item):
        """Checks whether an entry with the given key is present in the data.

        Args:
            key (any): The key to look for in the session data.

        Returns:
            bool: Whether an entry with the given key is present.

        Contract:
            This method will lock the session's data lock.
        """
        with self._lock:
            return item in self._internal