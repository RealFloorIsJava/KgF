"""
Part of KgF.

Author: LordKorea
"""

import re
from collections import OrderedDict
from html import escape
from threading import RLock
from time import time


class Match:
    """ A match """

    # The minimum amount of players for a match
    _MINIMUM_PLAYERS = 3

    # The amount of points to win the game
    _WIN_CONDITION = 8

    # The maximum number of cards in a deck
    _MAXIMUM_CARDS_IN_DECK = 2000

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
    def get_match(pid):
        """ Retrieves the match of this player or None if not existing """
        matches = Match.get_all()
        for match in matches:
            if match.has_participant(pid):
                return match
        return None

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

    @staticmethod
    def perform_housekeeping():
        """ Performs housekeeping tasks like checking timers """
        matches = Match.get_all()
        for match in matches:
            match.check_participants()
            match.check_timer()
            if match.get_num_participants() == 0:
                Match.remove_match(match.get_id())

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

        # The deck for this match
        self._deck = []

        # The state of the match
        self._state = "PENDING"

        # The participants of the match
        self._participants = OrderedDict()

        # The chat of this match, tuples with type/message
        self._chat = [("SYSTEM", "<b>Match was created.</b>")]

    def put_in_pool(self):
        """ Puts this match in the match pool """
        Match.add_match(self.get_id(), self)

    def get_id(self):
        """ Retrieves the ID """
        with self._lock:
            return self._id

    def get_owner_nick(self):
        """ Retrieves the nickname of the owner """
        with self._lock:
            for id in self._participants:
                return self._participants[id].get_nickname()

    def get_num_participants(self):
        """ Retrieves the number of participants in the match """
        with self._lock:
            return len(self._participants)

    def has_participant(self, pid):
        """ Checks whether this match has a participant with the given ID """
        with self._lock:
            return pid in self._participants

    def has_started(self):
        """ Checks whether the match has already started """
        with self._lock:
            return self._state != "PENDING"

    def get_seconds_to_next_phase(self):
        """ Retrieves the number of seconds to the next phase (state) """
        with self._lock:
            return self._timer - time()

    def check_timer(self):
        """ Checks the timer and performs updates accordingly """
        # Refresh the timer when there are not enough participants while
        # the match has not started yet
        threshold = Match._THRESHOLD_PENDING_REFRESH
        with self._lock:
            if self._timer - time() < threshold and self._state == "PENDING":
                if len(self._participants) < Match._MINIMUM_PLAYERS:
                    self._timer = time() + Match._TIMER_PENDING
                    self._chat.append(("SYSTEM",
                                       "<b>There are not enough players, "
                                       "the timer has been restarted!</b>"))

    def check_participants(self):
        """ Checks the timeout timers of all participants """
        with self._lock:
            for id in self._participants.copy():
                part = self._participants[id]
                if part.timed_out():
                    self._chat.append((
                        "SYSTEM",
                        "<b>%s timed out.</b>" % part.get_nickname()))
                    del self._participants[id]
                    # TODO check status of participant and react accordingly

    def abandon_participant(self, pid):
        """ Removes the given participant from the match """
        with self._lock:
            if pid not in self._participants:
                return
            nick = self._participants[pid].get_nickname()
            self._chat.append(("SYSTEM",
                               "<b>%s left.</b>" % nick))
            del self._participants[pid]

    def get_participant(self, pid):
        """ Retrieves the match participant with the given ID """
        with self._lock:
            return self._participants.get(pid, None)

    def add_participant(self, part):
        """ Adds a participant to the match """
        id = part.get_id()
        nick = part.get_nickname()
        with self._lock:
            self._participants[id] = part
            self._chat.append(("SYSTEM", "<b>%s joined.</b>" % nick))

    def create_deck(self, data):
        """ Create a deck from the given input source """
        tsv_lines = re.split(r"\n|\r|\r\n", data)

        # Setup the counters for card requirements
        limits = {"STATEMENT": Match._MINIMUM_STATEMENT_CARDS,
                  "OBJECT": Match._MINIMUM_OBJECT_CARDS,
                  "VERB": Match._MINIMUM_VERB_CARDS}

        # Read all cards from the source
        left = Match._MAXIMUM_CARDS_IN_DECK
        for line in tsv_lines:
            # Remove whitespace
            line = line.strip()
            if line == "":
                continue

            # Ensure that cards have a TEXT<tab>TYPE format
            tsv = re.split(r"\t", line)
            if len(tsv) != 2:
                continue

            text = escape(tsv[0])
            type = tsv[1]
            if type not in ("STATEMENT", "OBJECT", "VERB"):
                continue

            # Check that the number of gaps fits for the given type
            gaps = text.count("_")
            if gaps > 0:
                if type != "STATEMENT":
                    # Gaps in a non-statement card are not allowed
                    continue
                if gaps > 3:
                    # More than three gaps are not supported
                    continue
            else:
                if type == "STATEMENT":
                    # Statement card without any gaps
                    continue

            # Add the card to the deck
            with self._lock:
                self._deck.append((type, text))
            limits[type] -= 1

            # Enforce the card limit
            left -= 1
            if left == 0:
                break

        # Ensure that all limits are met
        note_given = False
        for type in limits:
            needed = limits[type]
            while limits[type] > 0:
                limits[type] -= 1
                # Notify the participants that there are cards missing
                if not note_given:
                    note_given = True
                    with self._lock:
                        self._chat.append(("SYSTEM", (
                            "<b>Your deck is insufficient. Placeholder cards"
                            " have been added to the match.</b>")))

                # Add a placeholder card
                with self._lock:
                    self._deck.append((
                        type,
                        "Your deck needs at least %i more %s cards"
                        % (needed, type.lower())))

    def get_status(self):
        """ Retrieves the status of this match """
        with self._lock:
            state = self._state

        # Handle states with a static status message
        if state != "PICKING":
            return {"PENDING": "Waiting for players...",
                    "CHOOSING": "Players are choosing cards...",
                    "COOLDOWN": "The next round is about to start...",
                    "ENDING": "The match is ending..."}.get(state,
                                                            "<State Unknown>")

        # Get the picking player
        picker = "<unknown>"
        with self._lock:
            for id in self._participants:
                part = self._participants[id]
                if part.is_picking():
                    picker = part.get_nickname()
                    break

        return "%s is picking a winner..." % picker

    def is_ending(self):
        """ Checks whether this match is ending """
        with self._lock:
            return self._state == "ENDING"

    def is_choosing(self):
        """ Checks whether this match is in the choosing state """
        with self._lock:
            return self._state == "CHOOSING"

    def is_picking(self):
        """ Checks whether this match is in the winner picking state """
        with self._lock:
            return self._state == "PICKING"

    def has_card(self):
        """ Checks whether this match has a statement card selected """
        with self._lock:
            return self._current_card is not None

    def get_card(self):
        """ Retrieves the currently selected statement card """
        with self._lock:
            return self._current_card

    def count_gaps(self):
        """
        Retrieves the larger of 1 and the number of gaps on the current card.
        """
        with self._lock:
            if self._current_card is None:
                return 1
            return self._current_card[1].count("_")

    def retrieve_chat(self, offset=0):
        """ Retrieves the chat beginning at the given offset """
        offset = max(0, offset)
        res = []
        with self._lock:
            for id, msg in enumerate(self._chat):
                if id >= offset:
                    res.append({"id": id,
                                "type": msg[0],
                                "message": msg[1]})
        return res
