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


def test_create_message():
    """Tests whether the match creation message is sent."""
    match = Match()
    match.create_deck(card_set)
    assert len(match._chat) == 1
    assert match._chat[0][0] == "SYSTEM"
    assert match._chat[0][1] == "<b>Match was created.</b>"


def test_join_message():
    """Tests whether the participant join message is sent."""
    match = Match()
    match.create_deck(card_set)
    part = Participant("ID", "NICK")
    match.add_participant(part)
    assert len(match._chat) > 0
    assert match._chat[-1][0] == "SYSTEM"
    assert match._chat[-1][1] == "<b>NICK joined.</b>"


def test_leave_message():
    """Tests whether the participant leave message is sent."""
    match = Match()
    match.create_deck(card_set)
    part = Participant("ID", "NICK")
    match.add_participant(part)
    match.abandon_participant("ID")
    assert len(match._chat) > 0
    assert match._chat[-1][0] == "SYSTEM"
    assert match._chat[-1][1] == "<b>NICK left.</b>"


def test_timeout_message():
    """Tests the participant timeout message."""
    match = Match()
    match.create_deck(card_set)
    part = Participant("ID", "NICK")
    match.add_participant(part)
    part._timeout = 1
    match.put_in_pool()
    Match.perform_housekeeping()
    assert len(match._chat) > 0
    assert match._chat[-1][0] == "SYSTEM"
    assert match._chat[-1][1] == "<b>NICK timed out.</b>"
