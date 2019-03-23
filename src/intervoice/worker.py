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
async def handle_message(combo: utils.Handler, message: str):

    with eliot.start_action(action_type="parse_command"):
        tree = combo.parser.parse(message)

    command, args = parsing.extract(tree)
    function = combo.rule_name_to_function[command]

    with eliot.start_action(action_type="call_user_function"):
        return await function(args)


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
        message = json.loads(message_bytes.decode())
        try:
            with eliot.Action.continue_task(task_id=message["eliot_task_id"]):
                await handle_message(combo=message_handler, message=message["body"])
        except Exception:
            pass


@log.log_call
def main(import_paths: Tuple[str]):

    modules = collect_modules(import_paths)
    registry = parsing.combine_modules(modules)

    trio.run(functools.partial(async_main, message_handler=registry))
