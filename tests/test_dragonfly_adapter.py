import pytest

import voca.dragonfly_adapter



@pytest.mark.parametrize(
    "grammar,expected", [("hello", "hello"), ("count {numerals}", "count (zero|one|two)")]
)
def test_build(grammar, expected):
    context = voca.dragonfly_adapter.Context(
        wordlists={"numerals": ["zero", "one", "two"]}
    )
    result = voca.dragonfly_adapter.build(grammar, context)
    assert result == expected
