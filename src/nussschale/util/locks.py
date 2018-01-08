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

from functools import wraps
from typing import Any, Callable


_Decorator = Callable[[Callable], Callable]


def named_mutex(lck_name: str="_lock") -> _Decorator:
    """Decorates a class method / instance method to lock the (R)Lock.

    Args:
        lck_name: The name of the lock (class) member.

    Returns:
        The described decorator.
    """
    def decorator(f: Callable):
        @wraps(f)
        def wrapper(ref: Any, *args, **kwargs) -> Any:
            lck = getattr(ref, lck_name)
            with lck:
                return f(ref, *args, **kwargs)
        return wrapper
    return decorator


# Convenience decorator with default '_lock'
mutex = named_mutex()
