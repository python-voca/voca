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



def make_command(utterance, final=True):
    return {
        "status": 0,
        "segment": 0,
        "result": {"hypotheses": [{"transcript": utterance}], "final": final},
        "id": "eec37b79-f55e-4bf8-9afe-01f278902599",
    }
