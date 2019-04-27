import json

import pytest


from tests import test_intervoice
from tests import helpers


@pytest.mark.parametrize(
    "spec,expected",
    [
        ("baz", '"baz"'),
        ("<foo>", "foo"),
        ("[foo]", '["foo"]'),
        ("[<foo>]", "[foo]"),
        ("(foo|bar)", '("foo" | "bar")'),
        (
            "[(go to | jump | jump to)] line <n>",
            '[("go to" | "jump" | "jump to")] "line" n',
        ),
    ],
)
def test_convert_spec(spec, expected):
    got = caster_adapter.convert_spec(spec)
    print(repr(spec), repr(got), repr(expected))
    assert got == expected


@pytest.mark.usefixtures("virtual_display", "turtle_window")
def test_simple_caster():
    from intervoice import caster_adapter

    caster_adapter.patch_all()

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
        )

    expected = ["KEY_X"]
    assert typed == expected
