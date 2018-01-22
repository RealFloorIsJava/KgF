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

from collections import Mapping
from typing import Any, Dict, Generator, Generic, TypeVar


T = TypeVar("T")


class LowerCaseDict(Mapping, Generic[T]):
    """A dictionary with only lower-case strings as keys.

    Mixed and upper case keys are converted.
    """

    def __init__(self) -> None:
        """Constructor."""
        self._backing = {}  # type: Dict[str, T]

    def __getitem__(self, key: str) -> T:
        """Retrieves an item.

        Args:
            key: The key of the item.

        Returns:
            The associated value.
        """
        assert isinstance(key, str), "key is no string"
        return self._backing[key.lower()]

    def __setitem__(self, key: str, value: T) -> None:
        """Updates a mapping.

        Args:
            key: The key of the mapping.
            value: The value that will be associated with the key.
        """
        assert isinstance(key, str), "key is no string"
        self._backing[key.lower()] = value

    def __contains__(self, key: Any) -> bool:
        """Checks whether this dict contains the given key.

        Args:
            key: The key to check.

        Returns:
            Whether the key is present.
        """
        assert isinstance(key, str), "key is no string"
        return key.lower() in self._backing

    def __delitem__(self, key: str) -> None:
        """Deletes an item.

        Args:
            key: The key of the item.
        """
        assert isinstance(key, str), "key is no string"
        del self._backing[key.lower()]

    def __iter__(self) -> Generator[str, None, None]:
        """Returns an iterator for the dictionary.

        Returns:
            An iterator for the keys.
        """
        for x in self._backing:
            yield x

    def __len__(self) -> int:
        """Retrieves the length of this dictionary.

        Returns:
            The length.
        """
        return len(self._backing)
