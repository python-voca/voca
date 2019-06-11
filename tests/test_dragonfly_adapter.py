import pathlib

import pytest
import dragonfly

import voca.dragonfly_adapter
import voca.kag


@pytest.mark.parametrize(
    "spec,expected", [("hello", "hello"), ("count {numerals}", "count (zero|one|two)")]
)
def test_transform_spec(spec, expected):
    lexicon = voca.dragonfly_adapter.Lexicon(
        wordlists={"numerals": ["zero", "one", "two"]}
    )
    result = voca.dragonfly_adapter.transform_spec(spec, lexicon)
    assert result == expected


def test_kag():
    wordlists = {"numeral": ["one", "two", "three", "four"]}
    lexicon = voca.dragonfly_adapter.Lexicon(wordlists)

    spec_to_action = {"count {numeral}": "foo", "other {numeral}": "bar"}

    lexspecs = [
        voca.dragonfly_adapter.LexiconSpec(lexicon, spec)
        for spec in spec_to_action.keys()
    ]

    dragonfly_grammar = voca.dragonfly_adapter.build_dragonfly_grammar(lexspecs)

    # Load engine before instantiating rules/grammars!
    engine = dragonfly.engines.backend_kaldi.engine.KaldiEngine(
        model_dir=voca.kag.MODEL_DIR, tmp_dir=voca.kag.TMP_DIR
    )

    dragonfly.engines._default_engine = engine
    dragonfly.engines.get_engine = lambda: engine

    print("getting mic")
    audio = dragonfly.engines.backend_kaldi.audio.VADAudio(input_device_index=4)

    # Instantiate the Kaldi decoder.
    print("connecting")
    voca.kag.connect(engine, audio)

    print("loading")
    voca.kag.load_grammar(engine, dragonfly_grammar)

    print("Listening...")

    for utterance in voca.kag.do_recognition(engine):
        print(utterance.text, utterance.likelihood)


if __name__ == '__main__':
    test_kag()