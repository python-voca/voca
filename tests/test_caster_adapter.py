import json
import sys
import types
import os

import pytest

from intervoice import patching
from intervoice import caster_adapter

from tests import test_intervoice
from tests import helpers


@pytest.mark.parametrize(
    "spec,expected",
    [
        ("baz", '"baz"'),
        ("<foo>", "foo"),
        ("[foo]", '[ "foo" ]'),
        ("[<foo>]", "[foo]"),
        ("(foo|bar)", '( "foo" | "bar" )'),
        ("quux <narg>", '"quux" narg'),
        ("quux [<narg>]", '"quux" [narg]'),
        (
            "[( foo bar | baz | eggs spam )] ham <narg>",
            '[( "foo bar" | "baz" | "eggs spam" )] "ham" narg',
        ),
    ],
)
def test_convert_spec(spec, expected):
    got = caster_adapter.convert_spec(spec)
    print(repr(spec), repr(got), repr(expected))
    assert got == expected


@pytest.mark.usefixtures("virtual_display")
def test_simple_caster():
    from intervoice import caster_adapter

    utterances = ["simple"]

    rows = [
        test_intervoice.make_command(utterance, final=True) for utterance in utterances
    ]
    lines = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()

    with helpers.capture_keypresses() as typed:
        helpers.run(
            [
                "manage",
                "-i",
                "intervoice.plugins.basic",
                "-i",
                "intervoice.plugins.vscode",
            ],
            input=lines,
            env={"INTERVOICE_PATCH_CASTER": "1", **os.environ},
        )

    expected = ["KEY_X"]
    assert typed == expected


@pytest.mark.usefixtures("virtual_display", "hash_seed")
def test_caster_extras():
    from intervoice import caster_adapter

    utterances = ["scroll page up five"]

    rows = [
        test_intervoice.make_command(utterance, final=True) for utterance in utterances
    ]
    lines = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()

    with helpers.capture_keypresses() as typed:
        helpers.run(
            [
                "manage",
                "-i",
                "intervoice.plugins.basic",
                "-i",
                "intervoice.plugins.vscode",
            ],
            input=lines,
            env={"INTERVOICE_PATCH_CASTER": "1", **os.environ},
        )

    expected = ["KEY_LEFT_ALT", "KEY_PAGE_UP"] * 5
    assert typed == expected


@pytest.mark.usefixtures("virtual_display")
def test_patch_caster():

    namespace = types.SimpleNamespace(python=types.SimpleNamespace(x=1))

    mapping = {
        "castervoice.lib.utilities": {},
        "castervoice.lib.ccr": {},
        "castervoice.lib.ccr.python": {"python": namespace},
        "castervoice.lib.ccr.python.python": {
            "PythonNon": types.SimpleNamespace(mapping={"with": 1})
        },
    }
    finder = patching.make_finder(mapping)

    with patching.finder_patch(finder):
        # import castervoice.lib.ccr
        import castervoice.lib.ccr.python
        import castervoice.lib.ccr.python.python

        assert castervoice.lib.ccr.python.python.PythonNon.mapping["with"] == 1


@pytest.mark.usefixtures("virtual_display")
def test_patch_dragonfly():

    mapping = {"dragonfly": {"Repeat": 5}, "dragonfly.__init__": {}}
    finder = patching.make_finder(mapping)

    with patching.finder_patch(finder):
        from dragonfly import Repeat

        assert Repeat == 5


@pytest.mark.usefixtures("virtual_display")
def test_f_keys():

    from intervoice import caster_adapter

    utterances = ["go to definition"]

    rows = [
        test_intervoice.make_command(utterance, final=True) for utterance in utterances
    ]
    lines = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()

    with helpers.capture_keypresses() as typed:
        helpers.run(
            [
                "manage",
                "-i",
                "intervoice.plugins.basic",
                "-i",
                "intervoice.plugins.vscode",
            ],
            input=lines,
            env={"INTERVOICE_PATCH_CASTER": "1", **os.environ},
        )

    expected = ["KEY_F12"]
    assert typed == expected


@pytest.mark.usefixtures("virtual_display")
def test_more_keys():

    from intervoice import caster_adapter

    utterances = ["up", "down", "left", "right"]
    expected = ["KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT"]
    rows = [
        test_intervoice.make_command(utterance, final=True) for utterance in utterances
    ]
    lines = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()

    with helpers.capture_keypresses() as typed:
        helpers.run(
            [
                "manage",
                "-i",
                "intervoice.plugins.basic",
                "-i",
                "castervoice.apps.vscode",
            ],
            input=lines,
            env={"INTERVOICE_PATCH_CASTER": "1", **os.environ},
        )

    assert typed == expected


@pytest.mark.usefixtures("virtual_display")
def test_using_castervoice_apps():

    from intervoice import caster_adapter

    utterances = ["incremental reverse"]

    rows = [
        test_intervoice.make_command(utterance, final=True) for utterance in utterances
    ]
    lines = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()

    with helpers.capture_keypresses() as typed:
        helpers.run(
            [
                "manage",
                "-i",
                "intervoice.plugins.basic",
                "-i",
                "castervoice.apps.emacs",
            ],
            input=lines,
            env={"INTERVOICE_PATCH_CASTER": "1", **os.environ},
        )

    expected = ["KEY_LEFT_CTRL", "KEY_R"]
    assert typed == expected
