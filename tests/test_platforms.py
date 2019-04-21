import platform

from intervoice import platforms


def test_implementation():
    @platforms.implementation(platforms.Platform.LINUX)
    def get_platform():
        return "This is Linux"

    @platforms.implementation(platforms.Platform.DARWIN)
    def get_platform():
        return "This is Darwin"

    @platforms.implementation(platforms.Platform.WINDOWS)
    def get_platform():
        return "This is Windows"

    assert get_platform() == "This is " + platform.system()
