import contextlib
import subprocess
import sys
import time

import trio
import sneakysnek.recorder


def run(args, **kwargs):
    return subprocess.check_output(
        [sys.executable, "-m", "voca"] + args, **kwargs
    )


@contextlib.contextmanager
def capture_keypresses():
    captured = []

    def capture(event):
        if event.event == sneakysnek.keyboard_event.KeyboardEvents.DOWN:
            captured.append(event.keyboard_key.name)

    rec = sneakysnek.recorder.Recorder.record(capture)
    yield captured
    time.sleep(2)
    rec.stop()

@contextlib.asynccontextmanager
async def async_capture_keypresses():
    captured = []

    def capture(event):
        if event.event == sneakysnek.keyboard_event.KeyboardEvents.DOWN:
            captured.append(event.keyboard_key.name)

    rec = await trio.run_sync_in_worker_thread(sneakysnek.recorder.Recorder.record, capture)
    yield captured
    rec.stop()
