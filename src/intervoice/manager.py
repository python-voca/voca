import functools
import os
import itertools
import sys
import pathlib
import subprocess
import json

import attr
import trio
import eliot

from intervoice import plugins
from intervoice import utils
from intervoice import streaming
from intervoice import log


def find_modules(package):
    modules = []
    for path in package.__path__:
        for child in pathlib.Path(path).iterdir():
            if child.is_dir() or child.is_file() and child.suffix == ".py":
                rel_path = child.relative_to(path)
                name = ".".join(rel_path.parts[:-1] + (rel_path.stem,))
                module = package.__name__ + "." + name
                modules.append(module)
    return modules


def worker_cli(modules=None):
    if modules is None:
        modules = find_modules(plugins)

    prefix = [sys.executable, "-m", "intervoice", "worker"]
    command = prefix.copy()
    for module in modules:
        command += ["-i", module]
    return command


@log.log_call
async def delegate_messages(stream, child):
    async for message in streaming.TerminatedFrameReceiver(stream, b"\n"):
        with eliot.start_action() as action:
            wrapped_message = json.dumps(
                {
                    "eliot_task_id": action.serialize_task_id().decode(),
                    "body": message.decode(),
                }
            ).encode()
            await child.stdin.send_all(wrapped_message + b"\n")


@log.log_call
async def replay_child_messages(child):
    async for message_from_child in streaming.TerminatedFrameReceiver(
        child.stdout, b"\n"
    ):
        print(message_from_child.decode())


@log.log_call
async def delegate_stream(stream):

    async with trio.Process(
        worker_cli(), stdin=subprocess.PIPE, stdout=subprocess.PIPE
    ) as child:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(delegate_messages, stream, child)
            nursery.start_soon(replay_child_messages, child)


@log.log_call
async def async_main():
    stream = trio._unix_pipes.PipeReceiveStream(os.dup(0))
    await delegate_stream(stream)


@log.log_call
def main():
    trio.run(functools.partial(async_main))
