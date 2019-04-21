import importlib
import functools
import sys
import os
import textwrap
import json
import types


from typing import Iterable
from typing import List
from typing import Tuple


import eliot
import trio
import toml
import lark


from intervoice import utils
from intervoice import streaming
from intervoice import log
from intervoice import parsing


@log.log_call
async def handle_message(combo: utils.Handler, data: dict):
    message = data["result"]["hypotheses"][0]["transcript"]

    with eliot.start_action(action_type="parse_command") as action:

        tree = combo.parser.parse(message)

    commands = parsing.extract_commands(tree)

    for command in commands:
        rule_name, args = command.data, command.children
        function = combo.rule_name_to_function[rule_name]
        with eliot.start_action(
            action_type="run_command", command=rule_name, args=args, function=function
        ):
            await function(args)


@log.log_call
def collect_modules(import_paths: Iterable[str]) -> List[types.ModuleType]:
    modules = []
    for path in import_paths:
        modules.append(importlib.import_module(path))
    return modules


@log.log_call
async def async_main(message_handler: utils.Handler):
    stream = trio._unix_pipes.PipeReceiveStream(os.dup(0))
    receiver = streaming.TerminatedFrameReceiver(stream, b"\n")

    async for message_bytes in receiver:
        data = json.loads(message_bytes.decode())

        try:
            with eliot.Action.continue_task(
                task_id=data.get("eliot_task_id", "@")
            ) as action:
                await handle_message(combo=message_handler, data=data)
        except Exception as e:
            action.finish(e)
            raise

        sys.exit(0)


@log.log_call
def main(import_paths: Tuple[str]):

    modules = collect_modules(import_paths)
    registry = parsing.combine_modules(modules)

    trio.run(functools.partial(async_main, message_handler=registry))
