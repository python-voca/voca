import platform

from intervoice import platforms


@platforms.implementation(platforms.Platform.LINUX)
def get_platform():
    return "This is Linux"


@platforms.implementation(platforms.Platform.DARWIN)
def get_platform():
    return "This is Darwin"


@platforms.implementation(platforms.Platform.WINDOWS)
def get_platform():
    return "This is Windows"


def test_implementation():
    assert get_platform() == "This is " + platform.system()


def test_dict_accessible():
    assert len(set(get_platform.implementations)) == 3
