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
    When the mutex of a multideck is locked no other locks can be
    requested. Thus the multideck lock can not be part of any deadlock.
"""

from random import shuffle, randint
from threading import RLock
from typing import Generic, List, Optional, Set, TypeVar, cast

from nussschale.util.locks import mutex


T = TypeVar("T")
U = TypeVar("U")


class MultiDeck(Generic[T, U]):
    """A (refilling) deck used to make selection seem more 'random'."""

    def __init__(self, deck: List[T]) -> None:
        """Constructor.

        Args:
            deck: A list of objects having an 'id' property. The deck
                should be safe for random access at any given time.
        """
        self._lock = RLock()
        self._backing = deck  # type: List[T]
        self._queue = []  # type: List[T]
        self._contained = set()  # type: Set[U]

    @staticmethod
    def _id_of(o: T) -> U:
        """Fetches the ID of the given object.

        This method only exists to enable type checking to work while
        structural subtyping is not supported.

        Args:
             o: The object to get the ID from.

        Returns:
            The ID of the object.
        """
        id = o.id  # type: ignore
        return cast(U, id)

    @mutex
    def request(self, banned_ids: Set[U], wilds = None, cards_left = 0,
                banned_wilds: Set[U] = None) -> Optional[T]:
        """Requests a card from the multideck.

        Args:
            banned_ids: A set of IDs that may not be chosen.
            wilds: The multideck with the wild cards. Defaults to None
            cards_left: The number of cards remaining to be drawn
            banned_wilds: A set of IDs of wild cards that are aleady drawn

        Returns:
            The object that was selected. This might be None if the
            request can't be fulfilled.

        Contract:
            This method locks the deck's lock.
        """
        if wilds is not None:
            if randint(1, cards_left) <= len(wilds._queue):
                return wilds.request(banned_wilds)
        ptr = 0

        # Try to find a viable object
        while ptr < len(self._queue):
            obj = self._queue[ptr]
            if MultiDeck._id_of(obj) not in banned_ids:
                self._contained.remove(MultiDeck._id_of(obj))
                del self._queue[ptr]
                return obj
            ptr += 1

        # No object in the queue works... Need to refill queue!
        # Note: For backing decks that are only slightly bigger than the
        # set of banned ids this might result in less than optimal randomness.
        # However in practice, deck size does exceed the number of banned ids
        # by at least factor 2.
        pool = []
        for obj in self._backing:
            if MultiDeck._id_of(obj) not in self._contained:
                pool.append(obj)
        shuffle(pool)
        for obj in pool:
            self._contained.add(MultiDeck._id_of(obj))
            self._queue.append(obj)

        # Try to find a viable object again
        while ptr < len(self._queue):
            obj = self._queue[ptr]
            if MultiDeck._id_of(obj) not in banned_ids:
                self._contained.remove(MultiDeck._id_of(obj))
                del self._queue[ptr]
                return obj
            ptr += 1

        # Still no object found: Failure, as the queue is already maximal.
        return None
