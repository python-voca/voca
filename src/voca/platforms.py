import enum
import platform

from typing import Tuple
from typing import Callable


_name_to_function = {}


class System(enum.Enum):
    LINUX = enum.auto()
    WINDOWS = enum.auto()
    DARWIN = enum.auto()


def implementation(*which: Tuple[System]) -> Callable:
    """Decorator for functions that provide a platform-specific functionality."""

    def wrap(func: Callable) -> Callable:

        try:
            seen_function = _name_to_function[func.__name__]
        except KeyError:
            seen_function = func
            _name_to_function[func.__name__] = func

        func.implementations = getattr(seen_function, "implementations", {})

        for item in which:
            seen_function.implementations[item] = func

        system_enum_value = System[(platform.system().upper())]

        try:
            return seen_function.implementations[system_enum_value]
        except KeyError:
            return seen_function

    return wrap
