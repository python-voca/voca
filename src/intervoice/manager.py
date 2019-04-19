from __future__ import annotations

import functools
import os
import itertools
import sys
import pathlib
import subprocess
import json

from typing import List
from typing import Optional

import attr
import trio
import eliot

from intervoice import plugins
from intervoice import utils
from intervoice import streaming
from intervoice import log


def worker_cli(should_log, module_names: Optional[List[str]] = None) -> List[str]:
    if module_names is None:
        module_names = utils.plugin_module_paths()

    log_arg = "--log" if should_log else "--no-log"
    prefix = [sys.executable, "-m", "intervoice", log_arg, "worker"]
    command = prefix.copy()
    for module_name in module_names:
        command += ["-i", module_name]
    return command


@log.log_call
async def delegate_messages(stream: trio.abc.ReceiveStream, child: trio.Process):
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
async def replay_child_messages(child: trio.Process) -> None:
    async for message_from_child in streaming.TerminatedFrameReceiver(
        child.stdout, b"\n"
    ):
        print(message_from_child.decode())


@log.log_call
async def delegate_stream(
    stream: trio.abc.ReceiveStream,
    should_log: bool,
    module_names: Optional[List[str]] = None,
):

    async with trio.Process(
        worker_cli(should_log, module_names),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    ) as child:
        try:
            async with trio.open_nursery() as nursery:
                nursery.start_soon(delegate_messages, stream, child)
                nursery.start_soon(replay_child_messages, child)
        except trio.BrokenResourceError:
            pass

        return child


@log.log_call
async def async_main(should_log, module_names: Optional[List[str]]):
    stream = trio._unix_pipes.PipeReceiveStream(os.dup(0))
    default_module_names = None
    module_names = default_module_names
    while True:

        with eliot.start_action():
            child = await delegate_stream(stream, should_log, module_names)

        if child.returncode == 3:
            module_names = default_module_names
        elif child.returncode == 4:
            module_names = ["intervoice.plugins.startstop"]
        else:
            raise ValueError(child)


@log.log_call
def main(should_log, module_names: Optional[List[str]]):
    trio.run(functools.partial(async_main, should_log, module_names))
