"""Part of KgF.

MIT License
Copyright (c) 2017-2018 LordKorea
Copyright (c) 2018 Arc676/Alessandro Vinciguerra

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
from random import shuffle
from threading import RLock
from time import time

from model.multideck import MultiDeck
from nussschale.util.locks import mutex, named_mutex


class Match:
    """Represents a match.

    Attributes:
        id (int): The ID of the match. It should not be changed.
        current_card (obj): The currently selected card. Should not be changed.

    Class Attributes:
        frozen (bool): Whether matches are currently frozen, i.e. whether their
            state transitions are disabled.
    """

    # The minimum amount of players for a match
    _MINIMUM_PLAYERS = 3

    # The amount of points to win the game
    _WIN_CONDITION = 8

    # The maximum number of cards in a deck
    _MAXIMUM_CARDS_IN_DECK = 9999

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
    _registry = OrderedDict()  # type: OrderedDict
    _id_counter = 0

    # MutEx for the match registry
    # Locking this MutEx can't cause any other MutExes to be locked.
    _pool_lock = RLock()

    # Whether matches are currently frozen
    frozen = False

    # Records which players appear to be AFK
    # Counts the number of rounds in which each player did nothing
    afk_players = {}

    @classmethod
    @named_mutex("_pool_lock")
    def get_by_id(cls, id):
        """Retrieves a match by its ID.

        Args:
            id (int): The ID of the match.

        Returns:
            obj: The match with that ID or None.

        Contract:
            This method locks the match pool lock.
        """
        return Match._registry.get(id, None)

    @classmethod
    @named_mutex("_pool_lock")
    def get_all(cls):
        """Retrieves all matches.

        Returns:
            list: All matches that currently exist.

        Contract:
            This method locks the match pool lock.
        """
        return [match for match in Match._registry.values()]

    @classmethod
    def get_match_of_player(cls, pid):
        """Retrieves the match of this player or None if not existing.

        Args:
            pid (str): The ID of the player.

        Returns:
            obj: The match of that player or None.
        """
        matches = Match.get_all()
        for match in matches:
            if match.has_participant(pid):
                return match
        return None

    @classmethod
    @named_mutex("_pool_lock")
    def add_match(cls, id, match):
        """Adds a match to the pool.

        Args:
            id (int): The ID of the new match.
            match (obj): The match that will be added.

        Contract:
            This method locks the match pool lock.
        """
        Match._registry[id] = match

    @classmethod
    @named_mutex("_pool_lock")
    def remove_match(cls, id):
        """Removes a match from the pool.

        Args:
            id (int): The ID of the match.

        Contract:
            This method locks the match pool lock.
        """
        if id in Match._registry:
            del Match._registry[id]

    @classmethod
    @named_mutex("_pool_lock")
    def get_next_id(cls):
        """Retrieves an unused id.

        Returns:
            int: An unused ID.

        Contract:
            This method locks the match pool lock.
        """
        Match._id_counter += 1
        return Match._id_counter

    @classmethod
    def perform_housekeeping(cls):
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
                Match.remove_match(match.id)

    def __init__(self):
        """Constructor."""
        # MutEx for the current match
        # Locking this MutEx can cause the following mutexes to be locked:
        #  model.participant.Participant MutEx
        self._lock = RLock()

        # The ID of this match
        self.id = Match.get_next_id()

        # The timer of the match
        self._timer = time() + Match._TIMER_PENDING

        # The current card of the match
        self.current_card = None

        # The deck for this match
        self._deck = {}

        # The multidecks for improved random drawing
        self._multidecks = {}

        # The state of the match.
        # One of: PENDING, CHOOSING, PICKING, COOLDOWN, ENDING
        self._state = "PENDING"

        # The participants of the match (some of them may be spectators)
        self._participants = OrderedDict()

        # The chat of this match, tuples with type/message
        self._chat = [("SYSTEM", "<b>Match was created.</b>")]

    def put_in_pool(self):
        """Puts this match into the match pool."""
        Match.add_match(self.id, self)

    @mutex
    def get_owner_nick(self):
        """Retrieves the nickname of the owner (the first of the players).

        Returns:
            str: The nickname of the owner.

        Contract:
            This method locks the match's instance lock and the participant's
            lock.
        """
        for part in self.get_participants(False):
            return part.nickname
        return "<unknown>"

    @mutex
    def get_num_participants(self, include_specs=True):
        """Retrieves the number of participants in the match.

        Args:
            include_specs (bool): Whether to include spectators in the count.

        Returns:
            int: The number of participants in the match.

        Contract:
            This method locks the match's instance lock.
        """
        if not include_specs:
            return len(list(self.get_participants(False)))

        # Default case: including spectators
        return len(self._participants)

    @mutex
    def has_participant(self, pid):
        """Checks whether this match has a participant with the given ID.

        Args:
            pid (int): The ID of the participant.

        Returns:
            bool: Whether a participant with the given ID exists.

        Contract:
            This method locks the match's instance lock.
        """
        return pid in self._participants

    @mutex
    def can_view_choices(self):
        """Whether participants can view others card choices.

        Returns:
            bool: Whether participants can see unredacted cards of others.

        Contract:
            This method locks the match's instance lock.
        """
        return (self._state == "PICKING"
                or self._state == "COOLDOWN"
                or self._state == "ENDING")

    def get_seconds_to_next_phase(self):
        """Retrieves the number of seconds to the next phase (state).

        Returns:
            int: The number of remaining seconds to the next phase.
        """
        # Locking is not needed here as access is atomic.
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
            for part in self.get_participants(False):
                part.delete_chosen()

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

            # Determine if pick is possible
            can_pick = self._pick_possible()

            # Kick AFK players
            for (pid, afkRounds) in self.afk_players.items():
                if afkRounds >= 2:
                    # Kick player for doing nothing for two rounds
                    self.abandon_participant(pid, "was kicked for being AFK for two rounds.")

            # If no pick is possible (too few valid hands) then skip the round
            if not can_pick:
                self._chat.append(("SYSTEM",
                                   "<b>Too few valid choices!</b>"))
                # If the round is skipped only unchoose the cards without
                # deleting them
                for part in self.get_participants(False):
                    part.unchoose_all()
                self._set_state("COOLDOWN")
                return

            # Dynamically calculate the timer from the number of participants
            pick_time = Match._TIMER_PICKING
            pick_time += (self.get_num_participants(False)
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
        # Frozen matches regenerate their timer
        if Match.frozen:
            self._timer = time() + 59 * 61  # Freeze timer to 59:59
        else:
            with self._lock:
                if self._timer - time() > 59 * 60:  # > 59 minutes
                    self._timer = time() + 30  # Reset to 00:30

        n_players = self.get_num_participants(False)

        # Refresh the timer when there are not enough participants while
        # the match has not started yet
        threshold = Match._THRESHOLD_PENDING_REFRESH
        with self._lock:
            if self._state == "PENDING" and self._timer - time() < threshold:
                if n_players < Match._MINIMUM_PLAYERS:
                    self._timer = time() + Match._TIMER_PENDING
                    self._chat.append(("SYSTEM",
                                       "<b>There are not enough players, "
                                       "the timer has been restarted!</b>"))

        # Cancel matches with too few players
        with self._lock:
            if n_players < Match._MINIMUM_PLAYERS:
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
            Match.remove_match(self.id)

    @mutex
    def check_participants(self):
        """Checks the timeout timers of all participants.

        Contract:
            This method locks the match's instance lock and the participant's
            lock.
        """
        parts = [x for x in self._participants.items()]
        for pid, part in parts:
            if part.has_timed_out():
                self._chat.append((
                    "SYSTEM",
                    "<b>%s timed out.</b>" % part.nickname))
                if part.picking:
                    self.notify_picker_leave(pid)
                del self._participants[pid]

    @mutex
    def abandon_participant(self, pid, message="left."):
        """Removes the given participant from the match.

        Args:
            pid (str): The ID of the participant.

        Contract:
            This method locks the match's instance lock and the participant's
            lock.
        """
        if pid not in self._participants:
            return
        nick = self._participants[pid].nickname
        self._chat.append(("SYSTEM",
                           "<b>%s %s</b>" % (nick, message)))
        if self._participants[pid].picking:
            self.notify_picker_leave(pid)
        del self._participants[pid]

    @mutex
    def notify_picker_leave(self, pid):
        """Notifies the match that the picker with the given ID left.

        Args:
            pid (str): The ID of the picker.

        Contract:
            This method locks the match's instance lock and the participant's
            lock.
        """
        # Find the first participant as the default fallback
        fallback = None
        for part in self.get_participants(False):
            fallback = part
            break
        assert fallback is not None

        next = False
        found = False
        for ppid, part in self._participants.items():
            if part.spectator:
                continue
            if next:
                part.picking = True
                found = True
                break
            elif pid == ppid:
                next = True

        if not found:
            fallback.picking = True

        if self._state == "CHOOSING" or self._state == "PICKING":
            self._set_state("COOLDOWN")
            self._chat.append(("SYSTEM", "<b>The picker left!</b>"))

    @mutex
    def get_participant(self, pid):
        """Retrieves the match participant with the given ID.

        Args:
            pid (str): The ID of the participant.

        Returns:
            obj: The participant with the given ID (or None).

        Contract:
            This method locks the match's instance lock.
        """
        return self._participants.get(pid, None)

    @mutex
    def get_participants(self, include_specs=True):
        """Retrieves all participants in the match.

        Args:
            include_specs (bool): Whether to include spectators.

        Returns:
            list: All participants in the match.

        Contract:
            This method locks the match's instance lock.
        """
        parts = self._participants.values()
        if not include_specs:
            return filter(lambda x: not x.spectator, parts)
        return parts

    @mutex
    def add_participant(self, part):
        """Adds a participant to the match.

        Args:
            part (obj): The participant that should be added to the match.

        Raises:
            ExpectationException: If joining is not possible at this time.

        Contract:
            This method locks the match's instance lock.
        """
        if not self.can_join() and not part.spectator:
            raise ExpectationException()

        id = part.id
        nick = part.nickname
        self._participants[id] = part
        if not part.spectator:
            self._chat.append(("SYSTEM", "<b>%s joined.</b>" % nick))
            self.afk_players[id] = 0
        else:
            self._chat.append(("SYSTEM",
                               "<b>%s is now spectating.</b>" % nick))

        # Add a threshold to the timer if the match has not started yet
        if self._state == "PENDING":
            if self._timer - time() < Match._THRESHOLD_JOIN_BONUS:
                self._timer = time() + Match._THRESHOLD_JOIN_BONUS

    def create_deck(self, data):
        """Creates a deck from the given input source.

        Does also create the multidecks for the created deck.

        Args:
            data (str): The deck data.

        Returns:
            (bool, str): Whether creation was successful and a status message.

        Contract:
            The instance of the match may not yet be made available to other
            threads. No locking is performed.
        """
        tsv_lines = re.split(r"\n|\r|\r\n", data)

        # Setup the counters for card requirements
        limits = {"STATEMENT": Match._MINIMUM_STATEMENT_CARDS,
                  "OBJECT": Match._MINIMUM_OBJECT_CARDS,
                  "VERB": Match._MINIMUM_VERB_CARDS}

        # Card ID counters
        card_id_counter = 0

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
                return False, "invalid_format"

            text = escape(tsv[0])
            type = tsv[1]
            if type not in ("STATEMENT", "OBJECT", "VERB"):
                return False, "invalid_type"

            # Check that the number of gaps fits for the given type
            gaps = text.count("_")
            if gaps > 0:
                if type != "STATEMENT":
                    # Gaps in a non-statement card are not allowed
                    return False, "illegal_gap"
                if gaps > 3:
                    # More than three gaps are not supported
                    return False, "too_many_gaps"
            else:
                if type == "STATEMENT":
                    # Statement card without any gaps
                    return False, "statement_no_gap"

            # Add the card to the deck
            if type not in self._deck:
                self._deck[type] = []
            self._deck[type].append(Card(card_id_counter, type, text))
            card_id_counter += 1
            limits[type] -= 1

            # Enforce the card limit
            left -= 1
            if left == 0:
                break

        # Ensure that all limits are met
        for num in limits.values():
            if num > 0:
                return False, "deck_too_small"

        # Create multidecks
        for type in self._deck:
            self._multidecks[type] = MultiDeck[Card, int](self._deck[type])

        return True, "OK"

    @mutex
    def get_status(self):
        """Retrieves the status of this match.

        Returns:
            str: The current status text for the match.

        Contract:
            This method locks the match's lock and some participant locks.
        """
        state = self._state

        # Handle states with a static status message
        if state == "PENDING":
            return "Waiting for players..."
        elif state == "CHOOSING":
            return "Players are choosing cards..."
        elif state == "COOLDOWN":
            return "The next round is about to start..."
        elif state == "ENDING":
            return "The match is ending..."

        # The current state has to be PICKING
        # Get the picking player
        picker = "<unknown>"
        for part in self._participants.values():
            if part.picking:
                picker = part.nickname
                break

        return "%s is picking a winner..." % picker

    def is_ending(self):
        """Checks whether this match is ending.

        Returns:
            bool: Whether this match is ending.
        """
        # Locking is not needed here as access is atomic.
        return self._state == "ENDING"

    def is_choosing(self):
        """Checks whether this match is in the choosing state.

        Returns:
            bool: Whether this match is in the CHOOSING state.
        """
        # Locking is not needed here as access is atomic.
        return self._state == "CHOOSING"

    def is_picking(self):
        """Checks whether this match is in the winner picking state.

        Returns:
            bool: Whether this match is in the PICKING state.
        """
        # Locking is not needed here as access is atomic.
        return self._state == "PICKING"

    def can_join(self):
        """Checks whether new participants can join the match.

        Returns:
            bool: Whether participants can join.
        """
        # Locking is not needed here as access is atomic.
        return self._state in ("PENDING", "COOLDOWN")

    def has_card(self):
        """Checks whether this match has a statement card selected.

        Returns:
            bool: Whether a statement card is selected.
        """
        # Locking is not needed here as access is atomic.
        return self.current_card is not None

    @mutex
    def count_gaps(self):
        """Retrieves the number of gaps on the current card.

        If no card or an invalid card is selected, at least 1 is returned.

        Returns:
            int: The number of gaps on the currently selected card.

        Contract:
            This method locks the match's instance lock.
        """
        if self.current_card is None:
            return 1
        return max(1, self.current_card.text.count("_"))

    @mutex
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
        for id, msg in enumerate(self._chat):
            if id >= offset:
                res.append({"id": id,
                            "type": msg[0],
                            "message": msg[1]})
        return res

    @mutex
    def send_message(self, nick, msg):
        """Sends a user message to the chat of this match.

        Args:
            nick (str): The nickname of the user.
            msg (str): The message that is sent to the chat.

        Contract:
            This method locks the match's instance lock.
        """
        msg = re.sub("(https?://\\S+)",
                     "<a href=\"\\1\" target=\"_blank\">\\1</a>",
                     msg)
        self._chat.append(("USER", "<b>%s</b>: %s" % (nick, msg)))

    @mutex
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
        winner = None
        for part in self.get_participants(False):
            if part.picking or part.choose_count() < gc:
                continue
            if part.order == order:
                winner = part
                break
        if winner is None:
            return

        for part in self.get_participants(False):
            if part is winner:
                part.increase_score()
                nick = part.nickname
                self._chat.append(("SYSTEM",
                                   "<b>%s won the round!</b>" % nick))
                if part.score >= Match._WIN_CONDITION:
                    self._chat.append(("SYSTEM", "<b>Game over!</b>"))
                    self._chat.append(("SYSTEM",
                                       "<b>%s won the game!</b>" % nick))
                    self._set_state("ENDING")
                else:
                    self._set_state("COOLDOWN")
            else:
                part.delete_chosen()

    @mutex
    def check_choosing_done(self):
        """Checks whether choosing is complete.

        Choosing is complete if and only if every non-picker has selected
        sufficient hand cards.

        Contract:
            This method locks the match's instance lock and participant locks.
        """
        gc = self.count_gaps()
        for part in self.get_participants(False):
            if not part.picking and gc != part.choose_count():
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
        for part in self.get_participants(False):
            # Find players who haven't played
            if part.choose_count() > 0:
                n += 1
                self.afk_players[part.id] = 0
            elif not part.picking:
                self.afk_players[part.id] += 1
        return n >= 2

    def _unchoose_incomplete(self):
        """Unchooses incomplete hands.

        Hands are incomplete when there are less cards selected than gaps on
        the selected match card.

        Contract:
            The caller ensures that the match's lock is held when calling this
            method.
        """
        gc = self.count_gaps()
        for part in self.get_participants(False):
            if part.picking:
                continue
            if part.choose_count() < gc:
                part.unchoose_all()
                nick = part.nickname
                self._chat.append(("SYSTEM",
                                   "<b>%s failed to choose cards!</b>" % nick))

    def _replenish_hands(self):
        """Replenishes the hands of all participants.

        Contract:
            The caller ensures that the match's lock is held when calling this
            method.
        """
        for part in self.get_participants(False):
            part.replenish_hand(self._multidecks)

    def _select_match_card(self):
        """Selects a random statement card for this match.

        Contract:
            The caller ensures that the match's lock is held when calling this
            method.
        """
        # Prevent duplicates from occuring
        disallowed = set()
        if self.current_card is not None:
            disallowed.add(self.current_card.id)

        self.current_card = self._multidecks["STATEMENT"].request(disallowed)

    def _shuffle_participants(self):
        """Shuffles the internal order of the participants.

        Contract:
            The caller ensures that the match's lock is held when calling this
            method.
        """
        # Create a random order
        order = list(range(self.get_num_participants(False)))
        shuffle(order)

        # Assign the order
        k = 0
        for part in self.get_participants(False):
            part.order = order[k] + 1
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
        fallback = None
        for part in self.get_participants(False):
            fallback = part
            break
        assert fallback is not None

        # Try to make the participant after the current one the new picker
        next = False
        for part in self.get_participants(False):
            if next:
                part.picking = True
                return
            elif part.picking:
                next = True
                part.picking = False

        # No picker was set yet
        fallback.picking = True


class Card:
    """Represents a card in the match's deck.

    Attributes:
        id (int): A unique ID for the card.
        type (str): The type of the card. Should not be modified.
        text (str): The text that is written on the card. Should not be
            modified.
    """

    def __init__(self, id, type, text):
        """Constructor.

        Args:
            id (int): A unique ID for the card.
            type (str): The type of the card.
            text (str): The text of the card.
        """
        self.id = id
        self.type = type
        self.text = text


class ExpectationException(Exception):
    """Raised if an expectation with which a method was called doesn't hold."""
    pass
