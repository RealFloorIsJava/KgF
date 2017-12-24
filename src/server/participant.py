"""
Part of KgF.

Author: LordKorea
"""

from collections import OrderedDict
from threading import RLock


class Participant:
    """ A participant in a match """

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
        self._timeout = 0

        # The order of this participant (may change each round)
        self._order = None

        # The hand of this participant
        self._hand = OrderedDict()

    def get_nickname(self):
        """ Retrieves the nickname of this participant """
        with self._lock:
            return self._nickname
