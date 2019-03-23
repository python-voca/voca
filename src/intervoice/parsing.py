from __future__ import annotations


import textwrap
import types

from typing import Tuple
from typing import List
from typing import Iterable


import lark


from intervoice import log
from intervoice import utils


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
def build_rules(registry: utils.Registry) -> List[utils.Rule]:
    rules = []
    for i, (pattern, function) in enumerate(registry.pattern_to_function.items()):
        name = f"rule_{i}"
        rules.append(utils.Rule(name=name, pattern=pattern, function=function))

    return rules


@log.log_call
def build_grammar(registry: utils.Registry, rules: List[utils.Rule]) -> str:

    start = "?start : message"

    message = "?message : " + "|".join(rule.name for rule in rules)

    rules_segment = "\n".join([f"{rule.name}:{rule.pattern}" for rule in rules])
    patterns_segment = "\n".join([f"{k}:{v}" for k, v in registry.patterns.items()])
    body = "\n".join([message, rules_segment, patterns_segment])

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
def combine_modules(modules: Iterable[types.ModuleType]):
    registry = utils.Registry()
    for module in modules:
        registry.pattern_to_function.update(module.registry.pattern_to_function)
        registry.patterns.update(module.registry.patterns)

    rules = build_rules(registry)
    grammar = build_grammar(registry, rules)

    rule_name_to_function = {rule.name: rule.function for rule in rules}

    parser = lark.Lark(
        grammar, debug=True, lexer="dynamic_complete", maybe_placeholders=True
    )

    return utils.Handler(
        registry=registry, parser=parser, rule_name_to_function=rule_name_to_function
    )
