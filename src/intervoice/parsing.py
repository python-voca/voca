from __future__ import annotations

import re
import textwrap
import types
import unicodedata

from typing import Tuple
from typing import List
from typing import Iterable


import lark


from voca import log
from voca import utils


class Transformer(lark.Transformer):
    def chord(self, arg):
        return arg[0]

    def key(self, arg):

        return arg[0]

    text = list


@log.log_call
def extract(tree: lark.Tree) -> Tuple[str, List]:
    tree = Transformer().transform(tree)
    return tree.data, tree.children


@log.log_call
def extract_commands(tree: lark.Tree) -> Tuple[str, List]:
    tree = Transformer().transform(tree)

    return tree.children


def _replace_match(match):
    body = unicodedata.name(match.group(0)).replace(" ", "_")
    return f"_{body}_"


@log.log_call
def normalize_pattern(text):

    return re.sub(r"\W", _replace_match, text).lower()


@log.log_call
def build_rules(registry: utils.Registry) -> List[utils.Rule]:
    rules = []
    for i, (pattern, function) in enumerate(registry.pattern_to_function.items()):
        normalized_pattern = normalize_pattern(pattern)
        name = f"rule_{i}__{normalized_pattern}"
        rules.append(utils.Rule(name=name, pattern=pattern, function=function))

    return rules


@log.log_call
def build_grammar(registry: utils.Registry, rules: List[utils.Rule]) -> str:

    start = "?start : message_group"

    message_group = "message_group : message+"

    message = "?message : " + "|".join(rule.name for rule in rules)

    rules_segment = "\n".join([f"{rule.name} : {rule.pattern}" for rule in rules])
    patterns_segment = "\n".join([f"{k} : {v}" for k, v in registry.patterns.items()])
    body = "\n".join([message_group, message, rules_segment, patterns_segment])

    imports = textwrap.dedent(
        """\


        %import common.ESCAPED_STRING
        %import common.SIGNED_NUMBER
        %import common.WS
        %import common.CNAME -> NAME
        %import common.NUMBER
        %import common.WS_INLINE

        %ignore WS

        """
    )
    return "\n".join([start, body, imports])


@log.log_call
def combine_modules(modules: Iterable[utils.PluginModule]):

    wrapper_group = utils.WrapperGroup()
    for module in modules:
        wrapper_group.wrappers.append(module.wrapper)

    return wrapper_group


def combine_registries(registries):
    combined = utils.Registry()
    for registry in registries:
        combined.pattern_to_function.update(registry.pattern_to_function)
        combined.patterns.update(registry.patterns)
    return combined
