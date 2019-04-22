import os
import subprocess

import pytest

@pytest.fixture(name="virtual_display", scope="session")
def _virtual_display():

    original_display = os.environ.get("DISPLAY", None)
    name = ":4"
    os.environ["DISPLAY"] = name

    proc = subprocess.Popen(
        [
            "/usr/bin/Xvfb",
            f"{name}",
            "-screen",
            "0",
            "1920x1080x24+32",
            "-fbdir",
            "/var/tmp",
        ]
    )

    yield

    proc.terminate()

    if original_display is None:
        del os.environ["DISPLAY"]
    else:
        os.environ["DISPLAY"] = original_display
