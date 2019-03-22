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
from intervoice import parsing


@log.log_call
async def handle_message(combo, message):
    try:
        tree = combo.parser.parse(message)
    except lark.exceptions.UnexpectedCharacters:
        eliot.write_traceback(exc_info=sys.exc_info())
        return

    command, args = parsing.extract(tree)
    function = combo.rule_name_to_function[command]
    try:
        return await function(args)
    except Exception as e:
        eliot.write_traceback(exc_info=sys.exc_info())


@log.log_call
def collect_modules(import_paths):
    modules = []
    for path in import_paths:
        modules.append(importlib.import_module(path))
    return modules


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
    registry = parsing.combine_modules(modules)
    handler = build_handler(registry)

    trio.run(
        functools.partial(async_main, message_handler=handler, stream_path=socket_path)
    )
