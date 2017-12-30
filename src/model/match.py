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
        Match Instance Lock -> Participant Lock

    The match pool mutex allows no other locks to be requested and therefor
    can not be part of any deadlock.
"""

import re
from collections import OrderedDict
from html import escape
from random import choice, shuffle
from threading import RLock
from time import time


class Match:
    """Represents a match."""

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
        """Retrieves a match by its ID.

        Args:
            id (int): The ID of the match.

        Returns:
            obj: The match with that ID or None.

        Contract:
            This method locks the match pool lock.
        """
        with Match._pool_lock:
            return Match._registry.get(id, None)

    @staticmethod
    def get_all():
        """Retrieves all matches.

        Returns:
            list: All matches that currently exist.

        Contract:
            This method locks the match pool lock.
        """
        with Match._pool_lock:
            res = []
            for k in Match._registry:
                res.append(Match._registry[k])
            return res

    @staticmethod
    def get_match(pid):
        """Retrieves the match of this player or None if not existing.

        Args:
            pid (int): The ID of the player.

        Returns:
            obj: The match of that player or None.

        Contract:
            This method locks the match pool lock.
            Independently, the locks of some matches will be locked.
        """
        matches = Match.get_all()
        for match in matches:
            if match.has_participant(pid):
                return match
        return None

    @staticmethod
    def add_match(id, match):
        """Adds a match to the pool.

        Args:
            id (int): The ID of the new match.
            match (obj): The match that will be added.

        Contract:
            This method locks the match pool lock.
        """
        with Match._pool_lock:
            Match._registry[id] = match

    @staticmethod
    def remove_match(id):
        """Removes a match from the pool.

        Args:
            id (int): The ID of the match.

        Contract:
            This method locks the match pool lock.
        """
        with Match._pool_lock:
            if id in Match._registry:
                del Match._registry[id]

    @staticmethod
    def get_next_id():
        """Retrieves an unused id.

        Returns:
            int: An unused ID.

        Contract:
            This method locks the match pool lock.
        """
        with Match._pool_lock:
            Match._id += 1
            return Match._id

    @staticmethod
    def perform_housekeeping():
        """Performs housekeeping tasks like checking timers.

        Contract:
            This method locks the match pool lock and match instance locks
            independently from each other.
        """
        matches = Match.get_all()
        for match in matches:
            match.check_participants()
            match.check_timer()
            if match.get_num_participants() == 0:
                Match.remove_match(match.get_id())

    def __init__(self):
        """Constructor."""
        # MutEx for the current match
        # Locking this MutEx can cause the following mutexes to be locked:
        #  model.participant.Participant MutEx
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
        """Puts this match into the match pool.

        Contract:
            This method locks the match pool lock and the instance lock
            independently.
        """
        Match.add_match(self.get_id(), self)

    def get_id(self):
        """Retrieves the ID of the match.

        Returns:
            int: The ID of this match.

        Contract:
            This method locks the match's instance lock.
        """
        with self._lock:
            return self._id

    def get_owner_nick(self):
        """Retrieves the nickname of the owner (the first of the players).

        Returns:
            str: The nickname of the owner.

        Contract:
            This method locks the match's instance lock and the participant's
            lock.
        """
        with self._lock:
            for id in self._participants:
                return self._participants[id].get_nickname()

    def get_num_participants(self):
        """Retrieves the number of participants in the match.

        Returns:
            int: The number of participants in the match.

        Contract:
            This method locks the match's instance lock.
        """
        with self._lock:
            return len(self._participants)

    def has_participant(self, pid):
        """Checks whether this match has a participant with the given ID.

        Args:
            pid (int): The ID of the participant.

        Returns:
            bool: Whether a participant with the given ID exists.

        Contract:
            This method locks the match's instance lock.
        """
        with self._lock:
            return pid in self._participants

    def has_started(self):
        """Checks whether the match has already started.

        Returns:
            bool: Whether the match has already started.

        Contract:
            This method locks the match's instance lock.
        """
        with self._lock:
            return self._state != "PENDING"

    def can_view_choices(self):
        """Whether participants can view others card choices.

        Returns:
            bool: Whether participants can see unredacted cards of others.

        Contract:
            This method locks the match's instance lock.
        """
        with self._lock:
            return (self._state == "PICKING"
                    or self._state == "COOLDOWN"
                    or self._state == "ENDING")

    def get_seconds_to_next_phase(self):
        """Retrieves the number of seconds to the next phase (state).

        Returns:
            int: The number of remaining seconds to the next phase.

        Contract:
            This method locks the match's instance lock.
        """
        with self._lock:
            return int(self._timer - time())

    def _set_state(self, state):
        """Updates the state for this match.

        Args:
            state (str): The new state the match will be in.

        Contract:
            The match's instance lock has to be locked when calling this
            method.
        """
        # Notification that the transition out of the old state takes place
        self._leave_state()
        self._state = state
        # Notification that the transition into the new state is finished
        self._enter_state()

    def _leave_state(self):
        """Handles a transition out of the current state.

        Contract:
            The match's instance lock has to be locked when calling this
            method.
        """
        if self._state == "COOLDOWN":
            # Delete all chosen cards from the hands
            for pid in self._participants:
                self._participants[pid].delete_chosen()

    def _enter_state(self):
        """Handles a transition into the current state.

        Contract:
            The match's instance loc has to be locked when calling this
            method.
        """
        if self._state == "CHOOSING":
            # Select a new picker
            self._select_next_picker()

            # Shuffle the order of the participants
            self._shuffle_participants()

            # Select a new statement card for the match
            self._select_match_card()

            # Replenish all hands
            self._replenish_hands()

            # Update the timer
            self._timer = time() + Match._TIMER_CHOOSING
        elif self._state == "PICKING":
            # Remove all hands that are not completed for picking
            self._unchoose_incomplete()

            # If no pick is possible (too few valid hands) then skip the round
            if not self._pick_possible():
                self._chat.append(("SYSTEM",
                                   "<b>Too few valid choices!</b>"))
                # If the round is skipped only unchoose the cards without
                # deleting them
                for pid in self._participants:
                    self._participants[pid].unchoose_all()
                self._set_state("COOLDOWN")
                return

            # Dynamically calculate the timer from the number of participants
            pick_time = Match._TIMER_PICKING
            pick_time += (len(self._participants)
                          * Match._TIMER_PICKING_BONUS_PER_PLAYER)
            self._timer = time() + pick_time
        elif self._state == "COOLDOWN":
            self._timer = time() + Match._TIMER_COOLDOWN
        elif self._state == "ENDING":
            self._timer = time() + Match._TIMER_ENDING

    def check_timer(self):
        """Checks the match timer and performs updates accordingly.

        Contract:
            This method locks the match pool lock and match instance lock.
        """
        # Refresh the timer when there are not enough participants while
        # the match has not started yet
        threshold = Match._THRESHOLD_PENDING_REFRESH
        with self._lock:
            if self._state == "PENDING" and self._timer - time() < threshold:
                if len(self._participants) < Match._MINIMUM_PLAYERS:
                    self._timer = time() + Match._TIMER_PENDING
                    self._chat.append(("SYSTEM",
                                       "<b>There are not enough players, "
                                       "the timer has been restarted!</b>"))

        # Cancel matches with too few players
        with self._lock:
            if len(self._participants) < Match._MINIMUM_PLAYERS:
                if self._state != "PENDING" and self._state != "ENDING":
                    self._set_state("ENDING")

        # Handle state transitions
        delete_match = False
        with self._lock:
            if time() > self._timer:
                if self._state == "PENDING":
                    self._set_state("CHOOSING")
                elif self._state == "CHOOSING":
                    self._set_state("PICKING")
                elif self._state == "PICKING":
                    self._chat.append(("SYSTEM",
                                       "<b>No winner was picked!</b>"))
                    self._set_state("COOLDOWN")
                elif self._state == "COOLDOWN":
                    self._set_state("CHOOSING")
                elif self._state == "ENDING":
                    delete_match = True

        # Delete the match if needed (note that it might already be deleted,
        # but deletion is idempotent)
        if delete_match:
            with self._lock:
                id = self._id
            Match.remove_match(id)

    def check_participants(self):
        """Checks the timeout timers of all participants.

        Contract:
            This method locks the match's instance lock and the participant's
            lock.
        """
        with self._lock:
            for id in self._participants.copy():
                part = self._participants[id]
                if part.timed_out():
                    self._chat.append((
                        "SYSTEM",
                        "<b>%s timed out.</b>" % part.get_nickname()))
                    if self._participants[id].is_picking():
                        self.notify_picker_leave(id)
                    del self._participants[id]

    def abandon_participant(self, pid):
        """Removes the given participant from the match.

        Args:
            pid (str): The ID of the participant.

        Contract:
            This method locks the match's instance lock and the participant's
            lock.
        """
        with self._lock:
            if pid not in self._participants:
                return
            nick = self._participants[pid].get_nickname()
            self._chat.append(("SYSTEM",
                               "<b>%s left.</b>" % nick))
            if self._participants[pid].is_picking():
                self.notify_picker_leave(pid)
            del self._participants[pid]

    def notify_picker_leave(self, pid):
        """Notifies the match that the picker with the given ID left.

        Args:
            pid (str): The ID of the picker.

        Contract:
            This method locks the match's instance lock and the participant's
            lock.
        """
        with self._lock:
            # Find the first participant as the default fallback
            for pid in self._participants:
                fallback = self._participants[pid]
                break

            next = False
            found = False
            for ppid in self._participants:
                if next:
                    self._participants[ppid].set_picking(True)
                    found = True
                    break
                elif pid == ppid:
                    next = True

            if not found:
                fallback.set_picking(True)

            if self._state == "CHOOSING" or self._state == "PICKING":
                self._set_state("COOLDOWN")
                self._chat.append(("SYSTEM", "<b>The picker left!</b>"))

    def get_participant(self, pid):
        """Retrieves the match participant with the given ID.

        Args:
            pid (str): The ID of the participant.

        Returns:
            obj: The participant with the given ID (or None).

        Contract:
            This method locks the match's instance lock.
        """
        with self._lock:
            return self._participants.get(pid, None)

    def get_participants(self):
        """Retrieves all participants in the match.

        Returns:
            list: All participants in the match.

        Contract:
            This method locks the match's instance lock.
        """
        res = []
        with self._lock:
            for id in self._participants:
                res.append(self._participants[id])
        return res

    def add_participant(self, part):
        """Adds a participant to the match.

        Args:
            part (obj): The participant that should be added to the match.

        Contract:
            This method locks the match's instance lock.
        """
        id = part.get_id()
        nick = part.get_nickname()
        with self._lock:
            self._participants[id] = part
            self._chat.append(("SYSTEM", "<b>%s joined.</b>" % nick))
            if self._timer - time() < Match._THRESHOLD_JOIN_BONUS:
                self._timer = time() + Match._THRESHOLD_JOIN_BONUS

    def create_deck(self, data):
        """Creates a deck from the given input source.

        Args:
            data (str): The deck data.

        Contract:
            This method locks the match's instance lock.
        """
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
                        self._chat.append(("SYSTEM",
                                           ("<b>Your deck is insufficient."
                                            " Placeholder cards have been"
                                            " added to the match.</b>")))

                # Add a placeholder card
                with self._lock:
                    self._deck.append((
                        type,
                        "Your deck needs at least %i more %s cards"
                        % (needed, type.lower())))

    def get_status(self):
        """Retrieves the status of this match.

        Returns:
            str: The current status text for the match.

        Contract:
            This method locks the match's lock and some participant locks.
        """
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
        """Checks whether this match is ending.

        Returns:
            bool: Whether this match is ending.

        Contract:
            This method locks the match's instance lock.
        """
        with self._lock:
            return self._state == "ENDING"

    def is_choosing(self):
        """Checks whether this match is in the choosing state.

        Returns:
            bool: Whether this match is in the CHOOSING state.

        Contract:
            This method locks the match's instance lock.
        """
        with self._lock:
            return self._state == "CHOOSING"

    def is_picking(self):
        """Checks whether this match is in the winner picking state.

        Returns:
            bool: Whether this match is in the PICKING state.

        Contract:
            This method locks the match's instance lock.
        """
        with self._lock:
            return self._state == "PICKING"

    def has_card(self):
        """Checks whether this match has a statement card selected.

        Returns:
            bool: Whether a statement card is selected.

        Contract:
            This method locks the match's instance lock.
        """
        with self._lock:
            return self._current_card is not None

    def get_card(self):
        """Retrieves the currently selected statement card.

        Returns:
            obj: The currently selected statement card.

        Contract:
            This method locks the match's instance lock.
        """
        with self._lock:
            return self._current_card

    def count_gaps(self):
        """Retrieves the number of gaps on the current card.

        If no card or an invalid card is selected, at least 1 is returned.

        Returns:
            int: The number of gaps on the currently selected card.

        Contract:
            This method locks the match's instance lock.
        """
        with self._lock:
            if self._current_card is None:
                return 1
            return max(1, self._current_card[1].count("_"))

    def retrieve_chat(self, offset=0):
        """Retrieves the chat beginning at the given offset.

        Args:
            offset (int, optional): The offset at which to start fetching chat
                messages.

        Returns:
            list: The chat messages that match the requirement.

        Contract:
            This method locks the match's instance lock.
        """
        offset = max(0, offset)
        res = []
        with self._lock:
            for id, msg in enumerate(self._chat):
                if id >= offset:
                    res.append({"id": id,
                                "type": msg[0],
                                "message": msg[1]})
        return res

    def send_message(self, nick, msg):
        """Sends a user message to the chat of this match.

        Args:
            nick (str): The nickname of the user.
            msg (str): The message that is sent to the chat.

        Contract:
            This method locks the match's instance lock.
        """
        with self._lock:
            self._chat.append(("USER",
                               "<b>%s</b>: %s" % (nick, msg)))

    def declare_round_winner(self, order):
        """Declares the participant with the given order winner for this round.

        Args:
            order (int): The order key of the participant that will be declared
                winner.

        Contract:
            This method locks the match's instance lock and the participant's
            lock.
        """
        gc = self.count_gaps()
        with self._lock:
            winner = None
            for pid in self._participants:
                part = self._participants[pid]
                if part.is_picking():
                    continue
                if part.choose_count() < gc:
                    continue
                if part.get_order() == order:
                    winner = part
                    break
            if winner is None:
                return
            for pid in self._participants:
                part = self._participants[pid]
                if part is winner:
                    part.increase_score()
                    nick = part.get_nickname()
                    self._chat.append(("SYSTEM",
                                       "<b>%s won the round!</b>" % nick))
                    if part.get_score() >= Match._WIN_CONDITION:
                        self._chat.append(("SYSTEM", "<b>Game over!</b>"))
                        self._chat.append(("SYSTEM",
                                           "<b>%s won the game!</b>" % nick))
                        self._set_state("ENDING")
                    else:
                        self._set_state("COOLDOWN")
                else:
                    part.delete_chosen()

    def check_choosing_done(self):
        """Checks whether choosing is complete.

        Choosing is complete if and only if every non-picker has selected
        sufficient hand cards.

        Contract:
            This method locks the match's instance lock and participant locks.
        """
        gc = self.count_gaps()
        with self._lock:
            for pid in self._participants:
                part = self._participants[pid]
                if not part.is_picking() and gc != part.choose_count():
                    return
            if self._timer - time() > Match._THRESHOLD_CHOOSING_FINISH:
                self._timer = time() + Match._THRESHOLD_CHOOSING_FINISH

    def _pick_possible(self):
        """ Checks whether picking a winner is possible.

        Picking is possible if there are at least two viable hands.

        Returns:
            bool: Whether picking a winner is possible.

        Contract:
            The caller ensures that the match's lock is held when calling this
            method.
        """
        n = 0
        for pid in self._participants:
            if self._participants[pid].choose_count() > 0:
                n += 1
                if n == 2:
                    return True
        return False

    def _unchoose_incomplete(self):
        """Unchooses incomplete hands.

        Hands are incomplete when there are less cards selected than gaps on
        the selected match card.

        Contract:
            The caller ensures that the match's lock is held when calling this
            method.
        """
        gc = self.count_gaps()
        for pid in self._participants:
            if self._participants[pid].is_picking():
                continue
            if self._participants[pid].choose_count() < gc:
                self._participants[pid].unchoose_all()
                nick = self._participants[pid].get_nickname()
                self._chat.append(("SYSTEM",
                                   "<b>%s failed to choose cards!</b>" % nick))

    def _replenish_hands(self):
        """Replenishes the hands of all participants.

        Contract:
            The caller ensures that the match's lock is held when calling this
            method.
        """
        for pid in self._participants:
            self._participants[pid].replenish_hand(self._deck)

    def _select_match_card(self):
        """Selects a random statement card for this match.

        Contract:
            The caller ensures that the match's lock is held when calling this
            method.
        """
        possible = [x for x in self._deck if x[0] == "STATEMENT"]
        self._current_card = choice(possible)

    def _shuffle_participants(self):
        """Shuffles the internal order of the participants.

        Contract:
            The caller ensures that the match's lock is held when calling this
            method.
        """
        # Create a random order
        order = list(range(self.get_num_participants()))
        shuffle(order)

        # Assign the order
        k = 0
        for pid in self._participants:
            self._participants[pid].set_order(order[k] + 1)
            k += 1

    def _select_next_picker(self):
        """Selects the next picker.

        If no picker is currently selected, the first participant will be the
        new picker.

        Contract:
            The caller ensures that the match's lock is held when calling this
            method.
        """
        # Find the first participant as the default fallback
        for pid in self._participants:
            fallback = self._participants[pid]
            break

        # Try to make the participant after the current one the new picker
        next = False
        for pid in self._participants:
            if next:
                self._participants[pid].set_picking(True)
                return
            elif self._participants[pid].is_picking():
                next = True
                self._participants[pid].set_picking(False)

        # No picker was set yet
        fallback.set_picking(True)
