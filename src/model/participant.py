"""Part of KgF.

MIT License
Copyright (c) 2017-2018 LordKorea

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
from copy import deepcopy
from threading import RLock
from time import time
from typing import Dict, List, Mapping, Optional, Set, TYPE_CHECKING, Union

from nussschale.util.locks import mutex


if TYPE_CHECKING:
    from model.match import Card
    from model.multideck import MultiDeck


class Participant:
    """Represents a participant in a match.

    Attributes:
        id: The ID of the participant. Should not be changed once the
            participant is created.
        nickname: The nickname of the participant. Should not be changed.
        picking: Whether the participant is picking.
        score: The score of the player. It is recommended to use the
            provided modification method to prevent race conditions from
            occurring.
        order: The order key of the particpant, used for shuffling.
        spectator: Whether the participant is a spectator.
        wants_skip: Whether the participant wants to skip the phase.
    """

    # The number of hand cards per type
    _HAND_CARDS_PER_TYPE = 6

    # The timeout timer after refreshing a participant, in seconds
    _PARTICIPANT_REFRESH_TIMER = 15

    def __init__(self, id: str, nickname: str) -> None:
        """Constructor.

        Args:
            id: The player's ID.
            nickname: The nickname that will be used for the player.
        """

        # MutEx for this participant
        # Locking this Mutex can cause no other mutexes to be locked
        self._lock = RLock()

        # The ID of this participant (player ID)
        self.id = id

        # The player nickname
        self.nickname = nickname

        # The score of this participant
        self.score = 0

        # Whether this participant is picking
        self.picking = False

        # The timeout timer of this participant
        self._timeout = time() + Participant._PARTICIPANT_REFRESH_TIMER

        # The order of this participant (may change each round)
        self.order = 0

        # Whether this participant is a spectator. Should not change after the
        # participant is part of a match.
        self.spectator = False

        # Whether the particpant wants to skip the phase.
        self.wants_skip = False

        # The hand of this participant
        self._hand = OrderedDict()  # type: Dict[int, HandCard]
        self._hand_counter = 1

    def has_timed_out(self) -> bool:
        """Checks whether this participant has timed out.

        Returns:
            Whether this client has timed out.
        """
        # Locking is not needed here as access is atomic.
        return time() >= self._timeout

    @mutex
    def increase_score(self) -> None:
        """Increases the score of this participant by one.

        Contract:
            This method locks the participant's lock.
        """
        assert not self.spectator, "Trying to increase score for spectator"
        self.score += 1

    def refresh(self) -> None:
        """Refreshes the timeout timer of this participant."""
        # Locking is not needed here as access is atomic.
        self._timeout = time() + Participant._PARTICIPANT_REFRESH_TIMER

    @mutex
    def unchoose_all(self) -> None:
        """Unchooses all cards on the hand of this participant.

        Contract:
            This method locks the participant's lock.
        """
        assert not self.spectator, "Trying to unchoose for spectator"
        for hcard in self._hand.values():
            hcard.chosen = None

    @mutex
    def delete_chosen(self) -> None:
        """Deletes all chosen hand cards from this participant.

        Contract:
            This method locks the participant's lock.
        """
        assert not self.spectator, "Trying to delete for spectator"
        del_list = []  # type: List[int]
        for hid, hcard in self._hand.items():
            if hcard.chosen is not None:
                del_list.append(hid)
        for hid in del_list:
            del self._hand[hid]

    @mutex
    def get_hand(self) -> Dict[int, "HandCard"]:
        """Retrieves a snapshot of the hand of this participant.

        Returns:
            A copy of the hand of the player.

        Contract:
            This method locks the participant's lock.
        """
        assert not self.spectator, "Trying to get hand for spectator"
        return deepcopy(self._hand)

    @mutex
    def choose_count(self) -> int:
        """Retrieves the number of chosen cards in the hand of this player.

        Returns:
            The number of cards in the hand.

        Contract:
            This method locks the participant's lock.
        """
        assert not self.spectator, "Trying to get count for spectator"
        n = 0
        for hcard in self._hand.values():
            if hcard.chosen is not None:
                n += 1
        return n

    @mutex
    def replenish_hand(self, mdecks: Mapping[str, "MultiDeck[Card, int]"],
                       wilds_in_play, cards_left) -> None:
        """Replenishes the hand of this participant from the given decks.

        Args:
            mdecks: Maps card type to a multideck of the card type.
            wilds_in_play: Number of wild cards currently in players' hands

        Contract:
            This method locks the participant's lock.
        """
        assert not self.spectator, "Trying to replenish spectator"

        # Find any wild cards already held
        banned_wilds = set()
        for hcard in self._hand.values():
            if hcard.card.type == "WILD":
                banned_wilds.add(hcard.card.id)

        # Replenish for every type
        for type in filter(lambda x: x != "STATEMENT" and x != "WILD", mdecks):
            # Count cards of that type and fetch IDs
            k_in_hand = 0
            ids_banned = set()  # type: Set[int]
            for hcard in self._hand.values():
                if hcard.card.type == type:
                    ids_banned.add(hcard.card.id)
                    k_in_hand += 1

            # Fill hand to limit
            for i in range(Participant._HAND_CARDS_PER_TYPE - k_in_hand):
                pick = mdecks[type].request(ids_banned, mdecks["WILD"],
                                            wilds_in_play, cards_left,
                                            banned_wilds)
                if pick is None:
                    break  # Can't fulfill the requirement...
                ids_banned.add(pick.id)
                self._hand[self._hand_counter] = HandCard(pick)
                self._hand_counter += 1

    @mutex
    def toggle_chosen(self, handid: int, allowance: int) -> None:
        """Toggles whether the hand card with the given ID is chosen.

        Args:
            handid: The ID of the hand card.
            allowance: The maximum number of cards that are allowed in
                the hand.

        Contract:
            This method locks the participant's lock.
        """
        assert not self.spectator, "Trying to toggle for spectator"

        # The next choice ID
        k = 0
        # The number of chosen hand cards
        n = 0
        for hcard in self._hand.values():
            if hcard.chosen is not None:
                n += 1
                k = max(k, hcard.chosen + 1)

        if handid in self._hand:
            hcard = self._hand[handid]
            if hcard.chosen is None:
                if n >= allowance:
                    return
                hcard.chosen = k
            else:
                k = hcard.chosen
                # Unselect the hand card and all with higher choice indexes
                for other_hcard in self._hand.values():
                    if (other_hcard.chosen is not None
                            and other_hcard.chosen >= k):
                        other_hcard.chosen = None

    @mutex
    def set_card_text(self, handid, text):
        """Changes the text on a given card. To be used for wild cards.

        Args:
            handid: The ID of the hand card.
            text: The new text for the card.

        Contract:
            This method locks the participant's lock.
        """
        self._hand[handid].card.text = text

    @mutex
    def get_choose_data(self, redacted: bool
                        ) -> List[Optional[Dict[str, Union[bool, str]]]]:
        """Fetches the choose data for this participant.

        Args:
            redacted: Whether the information should be redacted.

        Returns:
            The choose data for this participant.

        Contract:
            This method locks the participant's lock.
        """
        assert not self.spectator, "Trying to get data for spectator"

        data = []  # type: List[Optional[Dict[str, Union[bool, str]]]]
        for hcard in self._hand.values():
            type = hcard.card.type
            text = hcard.card.text
            chosen = hcard.chosen
            if chosen is not None:
                while len(data) <= chosen:
                    data.append(None)
                if redacted:
                    data[chosen] = {"redacted": True}
                else:
                    data[chosen] = {"type": type, "text": text}
        return data


class HandCard:
    """Represents a card on hand.

    Attributes:
        card: The card that this hand card represents. Should not be
            changed. Create a new HandCard if another card is required.
        chosen: The choice index of this hand card. If the card
            is not chosen it will be set to None.
    """

    def __init__(self, card: "Card") -> None:
        """Constructor.

        Args:
            card (obj): The card that this hand card represents.
        """
        self.card = card
        self.chosen = None  # type: Optional[int]
