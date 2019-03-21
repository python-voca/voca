import importlib
import functools
import sys
import os


import eliot
import trio
import toml


from intervoice import utils
from intervoice import streaming


@utils.log_call
async def handle_message(registry, message):

    command, *body = message.split()
    try:
        function = registry.mapping[command]
    except KeyError:
        eliot.Message.log(
            message_type="unknown_command", message=message, registry=registry
        )

        return
    with eliot.start_action(action_type="run_command", command=command, body=body):
        try:
            await function(body)
        except Exception:
            eliot.write_traceback(exc_info=sys.exc_info())


@utils.log_call
def collect_modules(import_paths):
    modules = []
    for path in import_paths:
        modules.append(importlib.import_module(path))
    return modules


@utils.log_call
def combine_modules(modules):
    registry = utils.Registry()
    for module in modules:
        registry.mapping.update(module.registry.mapping)
    return registry


@utils.log_call
def build_handler(registry):
    def message_handler(message):
        return handle_message(registry=registry, message=message)

    return lambda stream: streaming.handle_stream(message_handler, stream)


@utils.log_call
async def async_main(message_handler, stream_path):
    await streaming.serve_unix_domain(handler=message_handler, path=stream_path)


@utils.log_call
def main(import_paths, socket_path):

    modules = collect_modules(import_paths)
    registry = combine_modules(modules)
    handler = build_handler(registry)

    trio.run(
        functools.partial(async_main, message_handler=handler, stream_path=socket_path)
    )
