import contextlib
import os
import json
import secrets
import subprocess
import string
import textwrap

from click.testing import CliRunner
import pytest

from voca import cli

from tests import helpers
from tests.helpers import make_command


def test_main():
    runner = CliRunner()
    result = runner.invoke(cli.cli, [])

    assert result.output.startswith("Usage")
    assert result.exit_code == 0


@pytest.mark.usefixtures("virtual_display")
def test_strict():
    """Strict mode, not eager mode, executes final commands."""
    utterances = ["say alpha", "say bravo", "mode", "say charlie", "say delta"]

    rows = [make_command(utterance, final=True) for utterance in utterances]
    lines = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()

    with helpers.capture_keypresses() as typed:
        helpers.run(["manage", "-i", "voca.plugins.basic"], input=lines)

    expected = ["KEY_A", "KEY_B"]
    assert typed == expected


@pytest.mark.usefixtures("virtual_display")
def test_eager():
    """Eager mode, not strict mode, executes non-final commands."""
    utterances = ["say alpha", "say bravo", "mode", "say charlie", "say delta"]

    rows = [make_command(utterance, final=False) for utterance in utterances]
    lines = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()

    with helpers.capture_keypresses() as typed:
        helpers.run(["manage", "-i", "voca.plugins.basic"], input=lines)

    expected = ["KEY_C", "KEY_D"]
    assert typed == expected


@pytest.mark.usefixtures("virtual_display", "turtle_window")
def test_context_always():

    utterances = ["hit alpha", "hit bravo"]

    rows = [make_command(utterance, final=True) for utterance in utterances]
    lines = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()

    with helpers.capture_keypresses() as typed:
        helpers.run(
            [
                "manage",
                "-i",
                "voca.plugins.basic",
                "-i",
                "voca.plugins.yes",
                "-i",
                "voca.plugins.no",
            ],
            input=lines,
        )

    expected = ["KEY_D", "KEY_E", "KEY_F"] * 2
    assert typed == expected


@pytest.mark.usefixtures("virtual_display", "turtle_window")
def test_context_never():

    utterances = ["nope", "nope"]

    rows = [make_command(utterance, final=True) for utterance in utterances]
    lines = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()

    with helpers.capture_keypresses() as typed:
        helpers.run(["manage"], input=lines)

    expected = []
    assert typed == expected


@pytest.mark.usefixtures("virtual_display", "turtle_window")
def test_app_context_matches():
    """The spec is matched and the action is executed if the app is open."""

    utterances = ["check", "check"]

    rows = [make_command(utterance, final=True) for utterance in utterances]
    lines = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()

    with helpers.capture_keypresses() as typed:
        helpers.run(
            ["manage", "-i", "voca.plugins.basic", "-i", "voca.plugins.turtle_context"],
            input=lines,
        )

    expected = ["KEY_T", "KEY_U", "KEY_R", "KEY_T"] * 2
    assert typed == expected


@pytest.mark.usefixtures("virtual_display", "idle_window")
def test_app_context_does_not_match():
    """The spec is matched and the action is executed if the app is open."""

    utterances = ["check", "check"]

    rows = [make_command(utterance, final=True) for utterance in utterances]
    lines = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()

    with helpers.capture_keypresses() as typed:
        helpers.run(["manage"], input=lines)

    expected = []
    assert typed == expected


@pytest.mark.usefixtures("virtual_display")
def test_config_module(tmp_path):
    """Can add grammars from user config modules."""

    # Given
    source = textwrap.dedent(
        """\
        from voca import utils
        from voca.plugins import basic


        registry = utils.Registry()
        wrapper = utils.Wrapper(registry)


        @registry.register('"my config"')
        async def _type_xy(_):
            await basic.write("xy")
        """
    )

    user_modules_path = tmp_path / "user_modules"
    user_modules_path.mkdir()
    (user_modules_path / "my_module.py").write_text(source)

    # When
    utterances = ["my config"]
    rows = [make_command(utterance, final=True) for utterance in utterances]
    lines = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()

    with helpers.capture_keypresses() as typed:
        helpers.run(["manage", "-i", "user_modules.my_module"], input=lines)

    # Then
    expected = ["KEY_X", "KEY_Y"]
    assert typed == expected
