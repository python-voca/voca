import importlib
import functools
import sys

import trio
import toml

from intervoice import utils
from intervoice import reader


async def _handle_message(registry, message):
    command, *body = message.split()
    try:
        function = registry.mapping[command]
    except KeyError:
        print("Unknown command", message)
        return
    try:
        await function(body)
    except Exception:
        print(sys.exc_info())


def collect_modules(import_paths):
    modules = []
    for path in import_paths:
        modules.append(importlib.import_module(path))
    return modules


def combine_modules(modules):
    registry = utils.Registry()
    for module in modules:
        registry.mapping.update(module.registry.mapping)
    return registry


def build_handler(registry):
    message_handler = lambda message: _handle_message(
        registry=registry, message=message
    )
    return lambda stream: reader.handle_stream(message_handler, stream)


async def async_main(handle_message, stream_path):
    await reader.serve_unix_domain(handler=handle_message, path=stream_path)


def main(import_paths, socket_path):
    modules = collect_modules(import_paths)
    registry = combine_modules(modules)
    handler = build_handler(registry)
    trio.run(
        functools.partial(async_main, handle_message=handler, stream_path=socket_path)
    )
