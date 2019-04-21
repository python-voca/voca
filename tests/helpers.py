import subprocess
import sys


def run(args, **kwargs):
    return subprocess.check_output(
        [sys.executable, "-m", "intervoice"] + args, **kwargs
    )
