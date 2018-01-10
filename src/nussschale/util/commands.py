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

from traceback import extract_tb
from typing import Callable, Dict, Tuple, cast


class Command:
    """A command decorator.

    Attributes:
        name: The name of the command.
        desc: The description of the command.

    Class Attributes:
        commands: The registered commands, by name.
    """

    # Maps command names to commands
    commands = {}  # type: Dict[str, Command]

    def __init__(self, name: str, desc: str) -> None:
        """Constructor.

        Args:
            name: The name of the command.
            desc: The description of the command.
        """
        self.name = name
        self.desc = desc
        self._function = cast(Callable[[], None], None)

    def invoke(self) -> None:
        """Invokes the command."""
        try:
            self._function()
        except Exception as e:
            from nussschale.nussschale import nlog
            nlog().log("An error occurred while executing"
                       " command '%s'" % self.name)
            for entry in extract_tb(e.__traceback__):
                data = cast(Tuple[str, int, str, str],
                            tuple([entry[i] for i in range(4)]))
                nlog().log("\tFile \"%s\", line %i, in %s\n\t\t%s" % data)
            nlog().log(str(e))
            print("An error occurred - check the log for details.")

    def __call__(self, fn: Callable[[], None]) -> Callable[[], None]:
        """Decorates the command's function.

        Args:
            fn: The function that should be decorated.
        """
        assert self._function is None  # may not have been used yet!
        self._function = fn

        # At this point, release the command into the pool
        Command.commands[self.name] = self

        return fn
