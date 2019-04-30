import subprocess
import sys

from . import helpers


def test_mic_list():
    assert subprocess.check_output([sys.executable, "-m", "voca.mic", "-l"]).decode()
