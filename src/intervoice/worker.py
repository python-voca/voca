import importlib
import functools
import sys
import os
import textwrap
import json
import types
import shutil
import pathlib
import importlib.util

from typing import Iterable
from typing import List
from typing import Tuple

import appdirs
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
def load_from_path(import_path, filename):
    spec = importlib.util.spec_from_file_location(import_path, filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_module(import_path, backup_dir):
    """Import module and cache it in backup_dir, returning backup on failure."""
    try:
        with eliot.start_action(action_type="import_module", import_path=import_path):
            module = importlib.import_module(import_path)
    except Exception:
        sys.path.insert(0, str(backup_dir))
        try:
            module = importlib.import_module(import_path)
        except Exception:
            module = None
        finally:
            del sys.path[0]
    return module


@log.log_call
def collect_modules(import_paths: Iterable[str]) -> List[types.ModuleType]:
    backup_dir = pathlib.Path(appdirs.user_config_dir("intervoice")) / "backup_modules"

    modules = []
    for import_path in import_paths:
        module = get_module(import_path, backup_dir)

        if module is not None:
            modules.append(module)
            new_path = (backup_dir / import_path.replace(".", "/")).with_suffix(".py")
            new_path.parent.mkdir(exist_ok=True, parents=True)
            shutil.copy2(module.__file__, new_path)

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
