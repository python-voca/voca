import time
import os
import subprocess
import sys

import attr
import pytest


@attr.dataclass
class VirtualDisplay:
    name: str
    process: subprocess.Popen


@pytest.fixture(name="virtual_display", scope="session")
def _virtual_display():

    original_display = os.environ.get("DISPLAY", None)
    name = ":5"
    os.environ["DISPLAY"] = name

    proc = subprocess.Popen(
        ["/usr/bin/Xvfb", name, "-screen", "0", "1920x1080x24+32", "-fbdir", "/var/tmp"]
    )
    virtual_display = VirtualDisplay(name, proc)

    yield virtual_display

    proc.terminate()

    if original_display is None:
        del os.environ["DISPLAY"]
    else:
        os.environ["DISPLAY"] = original_display


@pytest.fixture(name="window_manager")
def _window_manager(virtual_display):
    proc = subprocess.Popen(["/usr/bin/i3"])
    time.sleep(1)
    yield

    proc.terminate()


@pytest.fixture(name="turtle_window")
def _turtle_window(window_manager):
    turtle = subprocess.Popen(["/usr/bin/python3", "-m", "turtle"])
    time.sleep(1)
    yield
    turtle.terminate()


@pytest.fixture(name="idle_window")
def _idle_window(window_manager):
    idle = subprocess.Popen(["/usr/bin/idle"])
    time.sleep(1)
    yield
    idle.terminate()
