"""
    Part of KgF.

    Author: LordKorea
"""

from threading import RLock
from uuid import uuid4
from time import time
from kgf import kconfig


class Session:
    """ Represents a client session """

    _pool_lock = RLock()

    # The currently existing sessions
    _sessions = {}

    @staticmethod
    def get_session(ip, sid=None):
        """
            Get an existing session or create a new one.
            Returns: (session, created?)
            A new session is created iff
                 - sid is None
              or - sid is unknown to the pool
              or - old session is expired
              or - the given ip is not the owner of the session
        """
        if sid is None:
            return Session(ip), True
        with Session._pool_lock:
            if sid not in Session._sessions:
                return Session(ip), True
            session = Session._sessions[sid]
            create = False
            if session.is_expired() or not session.is_owner(ip):
                del Session._sessions[sid]
                session = Session(ip)
                create = True
            return session, create

    def __init__(self, ip):
        self._lock = RLock()

        # Generate a random session ID
        self._sid = str(uuid4())
        self._ip = ip

        # Expires X minutes in the future
        self._expires = 0
        self.refresh()

        # Session data
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
            expire_time = int(kconfig().get("expire_time", "15"))
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
        self._lock = RLock()
        self._internal = {}
        self._nonce = None
        self.update_nonce()

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

    def check_nonce(self, nonce):
        """
            Compares the provided to the current nonce.
            True if equal, False otherwise
        """
        with self._lock:
            return self._nonce == nonce

    def get_nonce(self):
        """
            Gets the current nonce
        """
        with self._lock:
            return self._nonce

    def update_nonce(self):
        """
            Overwrites the old nonce with a new one and returns it
        """
        with self._lock:
            self._nonce = str(uuid4())
            return self._nonce
