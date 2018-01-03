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

from model.match import Match
from model.participant import Participant


card_set = ("_-0\tSTATEMENT\n_-1\tSTATEMENT\n_-2\tSTATEMENT\n_-3\tSTATEMENT\n"
            "_-4\tSTATEMENT\n_-5\tSTATEMENT\n_-6\tSTATEMENT\n_-7\tSTATEMENT\n"
            "_-8\tSTATEMENT\n_-9\tSTATEMENT\n"
            "O-0\tOBJECT\nO-1\tOBJECT\nO-2\tOBJECT\nO-3\tOBJECT\nO-4\tOBJECT\n"
            "O-5\tOBJECT\nO-6\tOBJECT\nO-7\tOBJECT\nO-8\tOBJECT\nO-9\tOBJECT\n"
            "V-0\tVERB\nV-1\tVERB\nV-2\tVERB\nV-3\tVERB\nV-4\tVERB\n"
            "V-5\tVERB\nV-6\tVERB\nV-7\tVERB\nV-8\tVERB\nV-9\tVERB\n")


def teardown_function(f):
    """Resets the match pool."""
    for k in [x for x in Match._registry]:
        del Match._registry[k]
    Match._id_counter = 0


def test_pool_size():
    """Tests whether the pool size is correct."""
    assert len(Match._registry) == 0
    match = Match()
    match.create_deck(card_set)
    match.put_in_pool()
    assert len(Match._registry) == 1
    Match.perform_housekeeping()
    assert len(Match._registry) == 0


def test_get_by_id():
    """Tests fetching a match by ID."""
    match = Match()
    assert Match.get_by_id(match.id) is None
    match.put_in_pool()
    assert Match.get_by_id(match.id) is match


def test_get_all():
    """Tests fetching all matches."""
    match = Match()
    match2 = Match()
    match.put_in_pool()
    match2.put_in_pool()
    assert match.id != match2.id
    matches = Match.get_all()
    assert len(matches) == 2
    assert (matches[0] is match) != (matches[1] is match)
    assert (matches[0] is match2) != (matches[1] is match2)


def test_get_match_of_player():
    """Tests fetching the match of a player."""
    match1 = Match()
    match2 = Match()
    part1 = Participant("1", "NICK")
    part2 = Participant("2", "NICK")
    part3 = Participant("3", "NICK")
    part4 = Participant("4", "NICK")
    match1.add_participant(part1)
    match1.add_participant(part3)
    match2.add_participant(part2)
    match2.add_participant(part4)
    match1.put_in_pool()
    match2.put_in_pool()
    mp1 = Match.get_match_of_player("1")
    mp2 = Match.get_match_of_player("2")
    mp3 = Match.get_match_of_player("3")
    mp4 = Match.get_match_of_player("4")
    assert mp1 is match1
    assert mp2 is match2
    assert mp3 is match1
    assert mp4 is match2


def test_remove_match():
    """Tests removing matches."""
    match = Match()
    match.put_in_pool()
    assert Match.get_by_id(match.id) is not None
    Match.remove_match(match.id)
    assert Match.get_by_id(match.id) is None


def test_get_next_id():
    """Tests retrieving new match IDs."""
    ids = set()
    for i in range(100):
        new_id = Match.get_next_id()
        assert new_id not in ids
        ids.add(new_id)
