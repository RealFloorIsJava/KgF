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
"""

from model.multideck import MultiDeck


class MockCard:
    """A mock card."""

    def __init__(self, id: int) -> None:
        """Constructor.

        Args:
            id: The ID of the mock card.
        """
        self.id = id


# Create a mock deck for testing
deck = []
deck_n = 20
for i in range(deck_n):
    deck.append(MockCard(i))


def test_multideck_period() -> None:
    """Tests the multideck's period with no restrictions placed on it."""
    md = MultiDeck(deck)
    ids = set()
    for i in range(deck_n):
        obj = md.request(set())
        assert obj is not None
        ids.add(obj.id)
    assert len(ids) == deck_n


def test_multideck_deplete() -> None:
    """Tests depleting the multideck by making restrictions more strict."""
    md = MultiDeck(deck)
    ids = set()
    for i in range(deck_n):
        obj = md.request(ids)
        assert obj is not None
        ids.add(obj.id)
    assert md.request(ids) is None


def test_multideck_draw() -> None:
    """Tests drawing objects from the multideck."""
    # Draw 5 times hands of deck_n/4 cards (must lead to duplicates)
    md = MultiDeck(deck)
    hands = []
    for i in range(5):
        hands.append(set())
        for j in range(deck_n // 4):
            obj = md.request(hands[i])
            assert obj is not None
            hands[i].add(obj.id)

    all_ids = set()
    for i in range(5):
        assert len(hands[i]) == deck_n // 4
        for x in hands[i]:
            all_ids.add(x)
    assert len(all_ids) == deck_n


def test_multideck_no_duplicate() -> None:
    """Tests the drawing for duplicates."""
    md = MultiDeck(deck)
    x = md.request(set())
    for i in range(deck_n - 1):
        obj = md.request(set())
        assert obj is not None and obj.id != x.id
