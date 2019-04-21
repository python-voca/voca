import contextlib
import os
import json
import secrets
import subprocess
import string

from click.testing import CliRunner
import sneakysnek.recorder
import pytest

from intervoice import cli

from tests import helpers


def test_main():
    runner = CliRunner()
    result = runner.invoke(cli.cli, [])

    assert result.output.startswith("Usage")
    assert result.exit_code == 0


def make_command(utterance, final=True):
    return {
        "status": 0,
        "segment": 0,
        "result": {"hypotheses": [{"transcript": utterance}], "final": final},
        "id": "eec37b79-f55e-4bf8-9afe-01f278902599",
    }


@contextlib.contextmanager
def capture_typed():
    captured = []

    def capture(event):
        if event.event == sneakysnek.keyboard_event.KeyboardEvents.DOWN:
            captured.append(event.keyboard_key.name)

    rec = sneakysnek.recorder.Recorder.record(capture)
    yield captured
    rec.stop()


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


@pytest.mark.usefixtures("virtual_display")
def test_strict():
    """Strict mode, not eager mode, executes final commands."""
    utterances = ["say alpha", "say bravo", "mode", "say charlie", "say delta"]

    rows = [make_command(utterance, final=True) for utterance in utterances]
    lines = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()

    with capture_typed() as typed:
        helpers.run(["manage"], input=lines)

    expected = ["KEY_A", "KEY_B"]
    assert typed == expected


@pytest.mark.usefixtures("virtual_display")
def test_eager():
    """Eager mode, not strict mode, executes non-final commands."""
    utterances = ["say alpha", "say bravo", "mode", "say charlie", "say delta"]

    rows = [make_command(utterance, final=False) for utterance in utterances]
    lines = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()

    with capture_typed() as typed:
        helpers.run(["manage"], input=lines)

    expected = ["KEY_C", "KEY_D"]
    assert typed == expected
