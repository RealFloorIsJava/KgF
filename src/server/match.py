"""
Part of KgF.

Author: LordKorea
"""

from collections import OrderedDict
from threading import RLock
from time import time


class Match:
    """ A match """

    # The minimum amount of players for a match
    _MINIMUM_PLAYERS = 3

    # The amount of points to win the game
    _WIN_CONDITION = 8

    # The minimum amount of cards of each type, don't set this to
    # lower than the number of cards on a hand
    _MINIMUM_STATEMENT_CARDS = 10
    _MINIMUM_OBJECT_CARDS = 10
    _MINIMUM_VERB_CARDS = 10

    # Timer constants, all values in seconds
    _TIMER_PENDING = 60
    _TIMER_CHOOSING = 60
    _TIMER_PICKING = 60
    _TIMER_COOLDOWN = 15
    _TIMER_ENDING = 20
    _TIMER_PENDING_JOIN_BONUS = 30
    _TIMER_PICKING_BONUS_PER_PLAYER = 7
    _TIMER_CHOOSING_FINAL = 10

    # Timer thresholds, all values in seconds
    _THRESHOLD_JOIN_BONUS = 30
    _THRESHOLD_PENDING_REFRESH = 10
    _THRESHOLD_CHOOSING_FINISH = 10

    # The match id -> match registry and the ID counter
    _registry = OrderedDict()
    _id = 0

    # MutEx for the match registry
    # Locking this MutEx can't cause any other MutExes to be locked.
    _pool_lock = RLock()

    @staticmethod
    def get_by_id(id):
        """ Retrieves a match by its ID """
        with Match._pool_lock:
            return Match._registry.get(id, None)

    @staticmethod
    def get_all():
        """ Retrieves all matches """
        with Match._pool_lock:
            res = []
            for k in Match._registry:
                res.append(Match._registry[k])
            return res

    @staticmethod
    def add_match(id, match):
        """ Adds a match to the pool """
        with Match._pool_lock:
            Match._registry[id] = match

    @staticmethod
    def remove_match(id):
        """ Removes a match from the pool """
        with Match._pool_lock:
            del Match._registry[id]

    @staticmethod
    def get_next_id():
        """ Fetches an unused id """
        with Match._pool_lock:
            Match._id += 1
            return Match._id

    def __init__(self):
        # MutEx for the current match
        # Locking this MutEx can cause the following mutexes to be locked:
        #  server.participant.Participant MutEx
        self._lock = RLock()

        # The ID of this match
        self._id = Match.get_next_id()

        # The timer of the match
        self._timer = time() + Match._TIMER_PENDING

        # The current card of the match
        self._current_card = None

        # The state of the match
        self._state = "PENDING"

        # The participants of the match
        self._participants = OrderedDict()

        # The chat of this match, tuples with type/message
        self._chat = []

        # Release the match into the pool
        Match.add_match(self._id, self)

    def get_id(self):
        """ Retrieves the ID """
        with self._lock:
            return self._id

    def get_owner_nick(self):
        """ Retrieves the nickname of the owner """
        with self._lock:
            return self._participants[0].get_nickname()  # TODO

    def get_num_participants(self):
        """ Retrieves the number of participants in the match """
        with self._lock:
            return len(self._participants)

    def has_started(self):
        """ Checks whether the match has already started """
        with self._lock:
            return self._state != "PENDING"

    def get_seconds_to_next_phase(self):
        """ Retrieves the number of seconds to the next phase (state) """
        with self._lock:
            return self._timer - time()
