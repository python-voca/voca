import random
import string
import time
import os
import types
import traceback

import kaldi_active_grammar
import dragonfly
import dragonfly.engines.backend_kaldi.engine

import logging

logging.basicConfig(level=10)
logging.getLogger("grammar.decode").setLevel(20)
logging.getLogger("compound").setLevel(20)
logging.getLogger("kaldi").setLevel(30)
logging.getLogger("engine").setLevel(10)
# logging.getLogger('kaldi').setLevel(10)

PROJECT_DIR = os.path.dirname(__file__)

MODEL_DIR = os.path.join(PROJECT_DIR, "kaldi_model_zamia")
TMP_DIR = os.path.join(PROJECT_DIR, "kald_tmp")


def load_grammar(engine, grammar):
    """ Load the given *grammar*. """

    # Dependency checking.
    memo = []
    for r in grammar._rules:
        for d in r.dependencies(memo):
            grammar.add_dependency(d)

    kaldi_rule_by_rule_dict = engine._compiler.compile_grammar(grammar, engine)
    wrapper = dragonfly.engines.backend_kaldi.engine.GrammarWrapper(
        grammar, kaldi_rule_by_rule_dict, engine
    )
    for kaldi_rule in list(kaldi_rule_by_rule_dict.values()):
        engine._decoder.add_grammar_fst(kaldi_rule.filepath)

    engine._grammar_wrappers[id(grammar)] = wrapper

    grammar._loaded = True


def finish_utterance(self):
    # end of phrase
    self._decoder.decode(b"", True)
    output, likelihood = self._decoder.get_output()
    output = self._compiler.untranslate_output(output).decode()
    kaldi_rule = self._parse_recognition(output)

    if self.audio_store and kaldi_rule:
        self.audio_store.finalize(output, kaldi_rule.grammar.name, kaldi_rule.rule.name)

    rule_name, _, text = output.partition(" ")
    return Utterance(rule_name, text, likelihood)


def _compute_kaldi_rules_activity(self):

    kaldi_rules_activity = [False] * self._compiler.num_kaldi_rules

    for grammar_wrapper in list(self._grammar_wrappers.values()):
        for kaldi_rule in list(grammar_wrapper.kaldi_rule_by_rule_dict.values()):
            if kaldi_rule.active:
                kaldi_rules_activity[kaldi_rule.id] = True

    return kaldi_rules_activity


def do_recognition(self, timeout=None, single=False):
    self._compiler.prepare_for_recognition()

    phrase_started = False

    for block in self._audio_iter:

        if block is not None:
            if not phrase_started:
                self._recognition_observer_manager.notify_begin()

                kaldi_rules_activity = _compute_kaldi_rules_activity(self)
                phrase_started = True
            else:
                kaldi_rules_activity = None
            self._decoder.decode(block, False, kaldi_rules_activity)
            if self.audio_store:
                self.audio_store.add_block(block)

        else:
            yield finish_utterance(self)

            phrase_started = False


def connect(self, audio=None):
    """ Connect to back-end SR engine. """
    if self._decoder:
        return

    if audio is None:
        audio = dragonfly.engines.backend_kaldi.audio.VADAudio(
            aggressiveness=self._vad_aggressiveness
        )

    self._log.debug("Loading KaldiEngine in process %s." % os.getpid())

    self._compiler = dragonfly.engines.backend_kaldi.compiler.KaldiCompiler(
        self._model_dir, self._tmp_dir
    )
    # self._compiler.fst_cache.invalidate()

    top_fst = self._compiler.compile_top_fst()
    dictation_fst_file = self._compiler.dictation_fst_filepath
    self._decoder = kaldi_active_grammar.KaldiAgfNNet3Decoder(
        model_dir=self._model_dir,
        tmp_dir=self._tmp_dir,
        top_fst_file=top_fst.filepath,
        dictation_fst_file=dictation_fst_file,
    )
    words = self._compiler.load_words()

    self._audio = audio
    self._audio_iter = self._audio.vad_collector(padding_ms=self._vad_padding_ms)
    self.audio_store = None

    self._any_exclusive_grammars = False


class Utterance:
    def __init__(self, rule_name, text, likelihood):
        self.rule_name = rule_name
        self.text = text
        self.likelihood = likelihood


# Always use CompoundRule or MappingRule, never base Rule!
class ExampleRule(dragonfly.CompoundRule):

    spec = "I see <food>"
    extras = [
        dragonfly.Choice(
            "food", {"(an | a juicy) apple": "good", "a [greasy] hamburger": "bad"}
        )
    ]

    def _process_recognition(self, node, extras):
        good_or_bad = extras["food"]
        print("That is a %s idea!" % good_or_bad)

    # def __getattribute__(self, name):
    #     print(self, name)
    #     return super(ExampleRule, self).__getattribute__(name)


def random_string(length):
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(length)
    )


def make_grammar(*args, **kwargs):
    name = kwargs.pop("name", None)
    if name is None:
        name = random_string(10)
    return dragonfly.Grammar(*args, name=name, **kwargs)


def make_dragonfly_rule(*args, **kwargs):
    name = kwargs.pop("name", None)
    if name is None:
        name = random_string(10)
    return dragonfly.CompoundRule(*args, name=name, **kwargs)


def main():

    # Load engine before instantiating rules/grammars!
    engine = dragonfly.engines.backend_kaldi.engine.KaldiEngine(
        model_dir=MODEL_DIR, tmp_dir=TMP_DIR
    )

    dragonfly.engines._default_engine = engine
    dragonfly.engines.get_engine = lambda: engine

    print("getting mic")
    audio = dragonfly.engines.backend_kaldi.audio.VADAudio(input_device_index=7)

    # Instantiate the Kaldi decoder.
    print("connecting")
    connect(engine, audio)

    rule = make_dragonfly_rule(
        spec="I see <food>",
        extras=[
            dragonfly.Choice(
                "food", {"(an | a juicy) apple": "good", "a [greasy] hamburger": "bad"}
            )
        ],
    )

    grammar = make_grammar()

    grammar._rules.append(rule)
    rule._grammar = grammar

    grammar.load = None

    print("loading")
    load_grammar(engine, grammar)

    print("Listening...")

    ######

    print("connecting")
    connect(engine, audio)

    grammar = make_grammar()

    grammar._rules.append(rule)

    rule2 = make_dragonfly_rule(spec="cat dog")

    grammar._rules.append(rule2)
    rule._grammar = grammar

    grammar.load = None

    print("loading")
    load_grammar(engine, grammar)

    print("Listening...")

    ######

    for utterance in do_recognition(engine):
        print(utterance.text, utterance.likelihood)


if __name__ == "__main__":
    main()
