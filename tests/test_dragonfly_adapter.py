import pytest

import voca.dragonfly_adapter



@pytest.mark.parametrize(
    "spec,expected", [("hello", "hello"), ("count {numerals}", "count (zero|one|two)")]
)
def test_transform_spec(spec, expected):
    lexicon = voca.dragonfly_adapter.Lexicon(
        wordlists={"numerals": ["zero", "one", "two"]}
    )
    result = voca.dragonfly_adapter.transform_spec(spec, lexicon)
    assert result == expected

