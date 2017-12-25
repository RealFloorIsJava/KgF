"""
Part of KgF.

Author: LordKorea
"""

from collections import OrderedDict
from threading import RLock
from time import time


class Participant:
    """ A participant in a match """

    # The timeout timer after refreshing a participant, in seconds
    _PARTICIPANT_REFRESH_TIMER = 15

    def __init__(self, id, nickname):
        # MutEx for this participant
        # Locking this MutEx can cause the following mutexes to be locked:
        #  TODO
        self._lock = RLock()

        # The ID of this participant (player ID)
        self._id = id

        # The player nickname
        self._nickname = nickname

        # The score of this participant
        self._score = 0

        # Whether this participant is picking
        self._picking = False

        # The timeout timer of this participant
        self._timeout = time() + Participant._PARTICIPANT_REFRESH_TIMER

        # The order of this participant (may change each round)
        self._order = None

        # The hand of this participant
        self._hand = OrderedDict()

    def get_id(self):
        """ Retrieves the ID of this participant """
        with self._lock:
            return self._id

    def get_nickname(self):
        """ Retrieves the nickname of this participant """
        with self._lock:
            return self._nickname

    def timed_out(self):
        """ Checks whether this participant has timed out """
        with self._lock:
            return time() >= self._timeout

    def is_picking(self):
        """ Checks whether this participant is picking cards """
        with self._lock:
            return self._picking

    def refresh(self):
        """ Refreshes the timeout timer of this participant """
        with self._lock:
            self._timeout = time() + Participant._PARTICIPANT_REFRESH_TIMER
