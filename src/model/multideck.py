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
    When the mutex of a multideck is locked no other locks can be
    requested. Thus the multideck lock can not be part of any deadlock.
"""

from random import shuffle
from threading import RLock

from util.locks import mutex


class MultiDeck:
    """One (refilling) deck used to make selection seem more 'random'."""

    def __init__(self, deck):
        """Constructor.

        Args:
            deck (list): A list of objects having an 'id' property. The deck
                should be safe for random access at any given time.
        """
        self._lock = RLock()
        self._backing = deck
        self._queue = []
        self._contained = set()

    @mutex
    def request(self, banned_ids):
        """Requests a card from the multideck.

        Args:
            banned_ids (set): A set of IDs that may not be chosen.

        Returns:
            obj: The object that was selected. This might be None if the
                request can't be fulfilled.

        Contract:
            This method locks the deck's lock.
        """
        ptr = 0

        # Try to find a viable object
        while ptr < len(self._queue):
            obj = self._queue[ptr]
            if obj.id not in banned_ids:
                self._contained.remove(obj.id)
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
            if obj.id not in self._contained:
                pool.append(obj)
        shuffle(pool)
        for obj in pool:
            self._contained.add(obj.id)
            self._queue.append(obj)

        # Try to find a viable object again
        while ptr < len(self._queue):
            obj = self._queue[ptr]
            if obj.id not in banned_ids:
                self._contained.remove(obj.id)
                del self._queue[ptr]
                return obj
            ptr += 1

        # Still no object found: Failure, as the queue is already maximal.
        return None
