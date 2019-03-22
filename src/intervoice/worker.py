import importlib
import functools
import sys
import os
import textwrap


import eliot
import trio
import toml
import lark


from intervoice import utils
from intervoice import streaming
from intervoice import log


class Transformer(lark.Transformer):
    def chord(self, arg):
        return arg[0]

    def key(self, arg):

        return arg[0]

    text = list



@log.log_call
def extract(tree):
    tree = Transformer().transform(tree)
    return tree.data, tree.children


@log.log_call
async def handle_message(combo, message):
    try:
        tree = combo.parser.parse(message)
    except lark.exceptions.UnexpectedCharacters:
        eliot.write_traceback(exc_info=sys.exc_info())
        return

    command, args = extract(tree)
    function = combo.rule_name_to_function[command]
    try:
        return await function(args)
    except Exception as e:
        eliot.write_traceback(exc_info=sys.exc_info())
        raise


@log.log_call
def collect_modules(import_paths):
    modules = []
    for path in import_paths:
        modules.append(importlib.import_module(path))
    return modules


@log.log_call
def build_rules(registry):
    rules = []
    for i, (pattern, function) in enumerate(registry.pattern_to_function.items()):
        name = f"rule_{i}"
        rules.append(utils.Rule(name=name, pattern=pattern, function=function))

    return rules


@log.log_call
def build_grammar(registry, rules):

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
def combine_modules(modules):
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


@log.log_call
def build_handler(combo):
    def message_handler(message):
        return handle_message(combo=combo, message=message)

    return lambda stream: streaming.handle_stream(message_handler, stream)


@log.log_call
async def async_main(message_handler, stream_path):
    await streaming.serve_unix_domain(handler=message_handler, path=stream_path)


@log.log_call
def main(import_paths, socket_path):

    modules = collect_modules(import_paths)
    registry = combine_modules(modules)
    handler = build_handler(registry)

    trio.run(
        functools.partial(async_main, message_handler=handler, stream_path=socket_path)
    )
