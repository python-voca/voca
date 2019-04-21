import enum
import platform

IMPLEMENTATIONS = {}


class Platform(enum.Enum):
    LINUX = enum.auto()
    WINDOWS = enum.auto()
    MACOS = enum.auto()


def check_platform(which):
    return platform.system() == which.name.capitalize()


def implementation(which):
    def wrap(func):
        if check_platform(which):
            IMPLEMENTATIONS[func.__name__] = func
            return func
        return IMPLEMENTATIONS.get(func.__name__)

    return wrap
