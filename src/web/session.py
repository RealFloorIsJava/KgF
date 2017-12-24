"""
Part of KgF.

Author: LordKorea
"""

from threading import RLock
from time import time
from uuid import uuid4

from kgf import kconfig


class Session:
    """ Represents a client session """

    # The MutEx for the session pool
    # Locking this MutEx can't cause any other MutExes to be locked.
    _pool_lock = RLock()

    # The session pool, all currently existing sessions, sid->session
    _sessions = {}

    @staticmethod
    def get_session(ip, sid=None):
        """
        Get an existing session or create a new one.
        Returns: (session, newly created?)
        A new session is created iff at least one of the following conditions
        holds:
             - sid is None
             - sid is unknown to the pool
             - old session is expired
             - the given ip is not the owner of the session
        """
        # Create new session if it was explicitly requested
        if sid is None:
            return Session(ip), True

        # Now search the pool for existing sessions
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
        """ Check whether the session has expired """
        with self._lock:
            return self._expires <= time()

    def is_owner(self, ip):
        """ Check whether the given ip is the owner of this session """
        with self._lock:
            return self._ip == ip

    def refresh(self):
        """ Refresh the session: reset expiration time """
        with self._lock:
            expire_time = kconfig().get("expire_time", 15)
            self._expires = time() + expire_time * 60

    def get_id(self):
        """ Return the session id """
        with self._lock:
            return self._sid

    def get_data(self):
        """ Get the session data """
        with self._lock:
            return self._data


class SessionData:
    """ Represents session data as a thread-safe dictionary """

    def __init__(self):
        # The MutEx for the session data
        # Locking this MutEx can't cause any other MutExes to be locked.
        self._lock = RLock()

        # The internals of the session data
        self._internal = {}

    def remove(self, key):
        with self._lock:
            del self._internal[key]

    def get(self, key, default=None):
        with self._lock:
            return self._internal.get(key, default)

    def __len__(self):
        with self._lock:
            return len(self._internal)

    def __getitem__(self, item):
        with self._lock:
            return self._internal[item]

    def __setitem__(self, key, value):
        with self._lock:
            self._internal[key] = value

    def __contains__(self, item):
        with self._lock:
            return item in self._internal
