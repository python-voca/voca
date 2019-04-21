import enum
import platform

_name_to_function = {}


class Platform(enum.Enum):
    LINUX = enum.auto()
    WINDOWS = enum.auto()
    DARWIN = enum.auto()


def implementation(which):
    def wrap(func):
        try:
            seen_function = _name_to_function[func.__name__]
        except KeyError:
            seen_function = func
            _name_to_function[func.__name__] = func
            seen_function.implementations = getattr(
                seen_function, "implementations", {}
            )

        seen_function.implementations[which] = func
        platform_enum_value = Platform[(platform.system().upper())]

        try:
            return seen_function.implementations[platform_enum_value]
        except KeyError:
            return seen_function

    return wrap
