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
    When the mutex of a participant is locked no other locks can be
    requested. Thus the participant lock can not be part of any deadlock.
"""

from collections import OrderedDict
from random import randint
from threading import RLock
from time import time


class Participant:
    """Represents a participant in a match."""

    # The number of hand cards per type
    _HAND_CARDS_PER_TYPE = 6

    # The timeout timer after refreshing a participant, in seconds
    _PARTICIPANT_REFRESH_TIMER = 15

    def __init__(self, id, nickname):
        """Constructor.

        Args:
            id (str): The player's ID.
            nickname (str): The nickname that will be used for the player.
        """

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
        """Retrieves the ID of this participant.

        Returns:
            str: The player's ID.

        Contract:
            This method locks the participant's lock.
        """
        with self._lock:
            return self._id

    def get_nickname(self):
        """Retrieves the nickname of this participant.

        Returns:
            str: The player's nickname.

        Contract:
            This method locks the participant's lock.
        """
        with self._lock:
            return self._nickname

    def timed_out(self):
        """Checks whether this participant has timed out.

        Returns:
            bool: Whether this client has timed out.

        Contract:
            This method locks the participant's lock.
        """
        with self._lock:
            return time() >= self._timeout

    def is_picking(self):
        """Checks whether the player is currently picking.

        Returns:
            bool: Whether the player is currently picking.

        Contract:
            This method locks the participant's lock.
        """
        with self._lock:
            return self._picking

    def set_picking(self, val):
        """(Un)marks this player as the picker.

        Args:
            val (bool): Whether this player should be the picker.

        Contract:
            This method locks the participant's lock.
        """
        with self._lock:
            self._picking = val

    def get_score(self):
        """Retrieves the score of this participant.

        Returns:
            int: The score of this participant.

        Contract:
            This method locks the participant's lock.
        """
        with self._lock:
            return self._score

    def increase_score(self):
        """Increases the score of this participant by one.

        Contract:
            This method locks the participant's lock.
        """
        with self._lock:
            self._score += 1

    def set_order(self, order):
        """Sets the order key of this participant to the given value.

        Args:
            order (int): The order key that will be used.

        Contract:
            This method locks the participant's lock.
        """
        with self._lock:
            self._order = order

    def get_order(self):
        """Retrieves the order key of this participant.

        Returns:
            The order key of this participant.

        Contract:
            This method locks the participant's lock.
        """
        with self._lock:
            return self._order

    def refresh(self):
        """Refreshes the timeout timer of this participant.

        Contract:
            This method locks the participant's lock.
        """
        with self._lock:
            self._timeout = time() + Participant._PARTICIPANT_REFRESH_TIMER

    def unchoose_all(self):
        """Unchooses all cards on the hand of this participant.

        Contract:
            This method locks the participant's lock.
        """
        with self._lock:
            for hid in self._hand:
                self._hand[hid][2] = None

    def delete_chosen(self):
        """Deletes all chosen hand cards from this participant.

        Contract:
            This method locks the participant's lock.
        """
        with self._lock:
            dl = []
            for hid in self._hand:
                if self._hand[hid][2] is not None:
                    dl.append(hid)
            for hid in dl:
                del self._hand[hid]

    def get_hand(self):
        """Retrieves a copy of the hand of this participant.

        Returns:
            dict: A copy of the hand of the player.

        Contract:
            This method locks the participant's lock.
        """
        with self._lock:
            return self._hand.copy()

    def choose_count(self):
        """Retrieves the number of chosen cards in the hand of this player.

        Returns:
            int: The number of cards in the hand.

        Contract:
            This method locks the participant's lock.
        """
        with self._lock:
            return len([x for x in self._hand if self._hand[x][2] is not None])

    def replenish_hand(self, deck):
        """Replenishes the hand of this participant from the given deck.

        Args:
            deck (list): The deck the cards are chosen from.

        Contract:
            This method locks the participant's lock.
        """
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
        """Toggles whether the hand card with the given ID is chosen.

        Args:
            handid (int): The ID of the hand card.
            allowance (int): The maximum number of cards that are allowed in
                the hand.

        Contract:
            This method locks the participant's lock.
        """
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
        """Fetches the choose data for this participant.

        Args:
            redacted (bool): Whether the information should be redacted.

        Returns:
            list: The choose data for this participant.

        Contract:
            This method locks the participant's lock.
        """
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
