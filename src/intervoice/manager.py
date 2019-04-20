from __future__ import annotations

import functools
import os
import itertools
import sys
import pathlib
import subprocess
import json
import contextlib
import copy

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
async def replay_child_messages(child: trio.Process) -> None:
    async for message_from_child in streaming.TerminatedFrameReceiver(
        child.stdout, b"\n"
    ):
        print(message_from_child.decode())


@log.log_call
def set_state(data, state):
    state = copy.deepcopy(state)
    body = data["result"]["hypotheses"][0]["transcript"]
    command, _space, _args = body.partition(" ")
    if command == "mode":
        state["modes"]["strict"] = not state["modes"]["strict"]
        return state

    return None


@log.log_call
async def delegate_task(data, worker, action):
    wrapped_data = dict(**data, eliot_task_id=action.serialize_task_id().decode())
    await worker.stdin.send_all(json.dumps(wrapped_data).encode() + b"\n")


@log.log_call
async def process_stream(receiver, pool):

    state = {"modes": {"strict": True}}
    workers = itertools.cycle(pool)
    async with trio.open_nursery() as nursery:
        async for message in receiver:
            with eliot.start_action() as action:
                # Handle state changes.
                data = json.loads(message.decode())
                maybe_new_state = set_state(data, state)
                if maybe_new_state is not None:
                    state = maybe_new_state
                    continue

                worker = next(workers)
                nursery.start_soon(delegate_task, data, worker, action)
                nursery.start_soon(replay_child_messages, worker)


@log.log_call
async def async_main(should_log, module_names: Optional[List[str]], num_workers=3):

    stream = trio._unix_pipes.PipeReceiveStream(os.dup(0))
    receiver = streaming.TerminatedFrameReceiver(stream, b"\n")

    default_module_names = None
    module_names = default_module_names

    pool = []
    async with contextlib.AsyncExitStack() as stack:
        for _ in range(num_workers):
            worker = await stack.enter_async_context(
                trio.Process(
                    worker_cli(should_log, module_names),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                )
            )
            pool.append(worker)

        await process_stream(receiver, pool)


@log.log_call
def main(should_log, module_names: Optional[List[str]]):
    trio.run(functools.partial(async_main, should_log, module_names))
