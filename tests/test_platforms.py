import platform

from voca import platforms


@platforms.implementation(platforms.System.DARWIN)
def get_platform():
    return "This is Darwin"


@platforms.implementation(platforms.System.LINUX)
def get_platform():
    return "This is Linux"


@platforms.implementation(platforms.System.WINDOWS)
def get_platform():
    return "This is Windows"


def test_implementation():
    assert get_platform() == "This is " + platform.system()


def test_dict_accessible():
    assert len(set(get_platform.implementations)) == 3
