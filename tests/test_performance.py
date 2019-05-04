import json
import subprocess
import sys
import os
import signal
import time

from tests import helpers


def test_manager_time():
    pid = os.getpid()
    sig = "SIGUSR1"
    num_utterances = 10
    utterances = [f"signal {pid} {sig}"] * num_utterances

    received_at = []

    def handler(_signum, _frame):
        received_at.append(time.perf_counter())

    signal.signal(signal.SIGUSR1, handler)

    rows = [helpers.make_command(utterance, final=True) for utterance in utterances]
    lines = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()
    proc = subprocess.Popen(
        [sys.executable, "-m", "voca", "manage", "-i" "voca.plugins.basic"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "VOCA_PATCH_CASTER": "1"},
    )

    # Wait for startup.
    time.sleep(1.0)

    start = time.perf_counter()

    try:
        proc.communicate(input=lines, timeout=2)
    except subprocess.TimeoutExpired:
        pass

    proc.terminate()

    durations = [when - start for when in received_at]

    assert len(durations) == num_utterances
    assert durations == sorted(durations)

    assert durations[0] < 0.05
    assert durations < [1.0] * num_utterances
