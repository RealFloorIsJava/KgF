"""Part of Nussschale.

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

from functools import update_wrapper
from typing import Callable, List


class Heartbeat:
    """A heartbeat decorator. Heartbeats will be run once per request.

    Class Attributes:
        heartbeats: The registered heartbeats.
    """

    # The registered heartbeats.
    heartbeats = []  # type: List[Callable[[], None]]

    def __init__(self, f: Callable[[], None]) -> None:
        """Constructor.

        Args:
            f: The function that should be wrapped.
        """
        Heartbeat.heartbeats.append(f)
        self._function = f
        update_wrapper(self, f)

    def __call__(self):
        """Implements calling the decorated function.

        Note: This is only used if a heartbeat function is called by hand.
        """
        self._function()
