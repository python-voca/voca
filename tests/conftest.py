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
    name = ":6"
    os.environ["DISPLAY"] = name

    proc = subprocess.Popen(
        ["/usr/bin/Xvfb", name, "-screen", "0", "1920x1080x24+32", "-fbdir", "/var/tmp"]
    )
    virtual_display = VirtualDisplay(name, proc)
    time.sleep(1.0)
    try:
        yield virtual_display
    finally:
        proc.terminate()

        if original_display is None:
            del os.environ["DISPLAY"]
        else:
            os.environ["DISPLAY"] = original_display


@pytest.fixture(name="window_manager")
def _window_manager(virtual_display):
    proc = subprocess.Popen(["/usr/bin/i3"])
    time.sleep(1)
    try:
        yield
    finally:
        proc.terminate()


@pytest.fixture(name="turtle_window")
def _turtle_window(window_manager):
    turtle = subprocess.Popen(["/usr/bin/python3", "-m", "turtle"])
    time.sleep(2)
    try:
        yield
    finally:
        turtle.terminate()


@pytest.fixture(name="idle_window")
def _idle_window(window_manager):
    idle = subprocess.Popen(["/usr/bin/idle"])
    time.sleep(1)
    try:
        yield
    finally:
        idle.terminate()


@pytest.fixture(name="hash_seed")
def _hash_seed():
    original_hash_seed = os.environ.get("PYTHONHASHSEED")
    os.environ["PYTHONHASHSEED"] = "123"
    try:
        yield
    finally:
        if original_hash_seed is None:
            del os.environ["PYTHONHASHSEED"]
        else:
            os.environ["PYTHONHASHSEED"] = original_hash_seed


@pytest.fixture(name="config_dir")
def _config_dir(tmp_path):
    os.environ["VOCA_CONFIG_DIR"] = str(tmp_path)
    return tmp_path
