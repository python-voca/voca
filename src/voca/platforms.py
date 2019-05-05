"""
Functions for implementing cross-platform functionality.
"""

import enum
import platform

from typing import Tuple
from typing import Callable

from voca import utils

_name_to_function = {}


@utils.public
class System(enum.Enum):
    LINUX = enum.auto()
    WINDOWS = enum.auto()
    DARWIN = enum.auto()


@utils.public
def implementation(*which: Tuple[System]) -> Callable:
    """Decorator for functions that provide a platform-specific functionality.

    To define a function ``create_new_window`` for multiple platforms, use the
    decorator:

    ::

        @implementation(System.LINUX)
        def create_new_window(name):
            return window(name)


        @implementation(System.WINDOWS)
        def create_new_window(name):
            return application(name)


    Then just call it with ``create_new_window()`` and the proper platform
    implementation will be called. Access the dictionary mapping platform to
    implementation function as ``create_new_window.implementations``.

    """

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
