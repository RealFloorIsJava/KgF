"""
Part of KgF.

Author: LordKorea
"""

from collections import OrderedDict
from random import randint
from threading import RLock
from time import time


class Participant:
    """ A participant in a match """

    # The number of hand cards per type
    _HAND_CARDS_PER_TYPE = 6

    # The timeout timer after refreshing a participant, in seconds
    _PARTICIPANT_REFRESH_TIMER = 15

    def __init__(self, id, nickname):
        # MutEx for this participant
        # Locking this Mutex can cause no other mutexes to be locked
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
        self._order = 0

        # The hand of this participant
        # Entries have the form [type, text, chosen]
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

    def set_picking(self, val):
        """ Changes whether this participant is picking """
        with self._lock:
            self._picking = val

    def get_score(self):
        """ Retrieves the score of this participant """
        with self._lock:
            return self._score

    def increase_score(self):
        """ Increases the score of this participant """
        with self._lock:
            self._score += 1

    def set_order(self, order):
        """ Sets the order of this participant """
        with self._lock:
            self._order = order

    def get_order(self):
        """ Retrieves the order of this participant """
        with self._lock:
            return self._order

    def refresh(self):
        """ Refreshes the timeout timer of this participant """
        with self._lock:
            self._timeout = time() + Participant._PARTICIPANT_REFRESH_TIMER

    def unchoose_all(self):
        """ Unchooses all cards on the hand """
        with self._lock:
            for hid in self._hand:
                self._hand[hid][2] = None

    def delete_chosen(self):
        """ Deletes all chosen hand cards from this participant """
        with self._lock:
            dl = []
            for hid in self._hand:
                if self._hand[hid][2] is not None:
                    dl.append(hid)
            for hid in dl:
                del self._hand[hid]

    def get_hand(self):
        """ Retrieves the hand of this participant """
        with self._lock:
            return self._hand.copy()

    def choose_count(self):
        """ Returns the number of chosen cards in the hand """
        with self._lock:
            return len([x for x in self._hand if self._hand[x][2] is not None])

    def replenish_hand(self, deck):
        """ Replenishes the hand of this participant from the given deck """
        with self._lock:
            kv = len([x for x in self._hand if self._hand[x][0] == "VERB"])
            ko = len([x for x in self._hand if self._hand[x][0] == "OBJECT"])
            # TODO improve this
            while kv < Participant._HAND_CARDS_PER_TYPE:
                x = randint(0, len(deck) - 1)
                while x in self._hand or deck[x][0] != "VERB":
                    x = randint(0, len(deck) - 1)
                self._hand[x] = [deck[x][0], deck[x][1], None]
                kv += 1
            while ko < Participant._HAND_CARDS_PER_TYPE:
                x = randint(0, len(deck) - 1)
                while x in self._hand or deck[x][0] != "OBJECT":
                    x = randint(0, len(deck) - 1)
                self._hand[x] = [deck[x][0], deck[x][1], None]
                ko += 1

    def toggle_chosen(self, handid, allowance):
        """ Toggles whether the hand card with the given ID is chosen """
        k = 0
        n = 0
        with self._lock:
            for hid in self._hand:
                if self._hand[hid][2] is not None:
                    n += 1
                    k = max(k, self._hand[hid][2] + 1)
            if handid in self._hand:
                if self._hand[handid][2] is None:
                    if n >= allowance:
                        return
                    self._hand[handid][2] = k
                else:
                    k = self._hand[handid][2]
                    for hid in self._hand:
                        if (self._hand[hid][2] is not None
                                and self._hand[hid][2] >= k):
                            self._hand[hid][2] = None

    def get_choose_data(self, redacted):
        """ Fetches the choose data for this participant """
        with self._lock:
            data = []
            for hid in self._hand:
                type, text, chosen = self._hand[hid]
                if chosen is not None:
                    while len(data) <= chosen:
                        data.append(None)
                    if redacted:
                        data[chosen] = {"redacted": True}
                    else:
                        data[chosen] = {"type": type,
                                        "text": text}
            return data
