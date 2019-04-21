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
async def delegate_task(data, worker, state, action):
    wrapped_data = dict(
        **data, state=state, eliot_task_id=action.serialize_task_id().decode()
    )
    await worker.stdin.send_all(json.dumps(wrapped_data).encode() + b"\n")


@attr.s
class Pool:
    max_workers: int = attr.ib(default=1)
    should_log: bool = attr.ib(default=True)
    module_names: list = attr.ib(factory=list)
    processes: set = attr.ib(factory=set)

    def start(self):
        for _ in range(self.max_workers):
            self.add_new_process()

    def get_process(self):
        return self.processes.pop()

    def add_new_process(self):
        self.processes.add(
            trio.Process(
                worker_cli(self.should_log, self.module_names),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
        )


@log.log_call
async def run_worker(data, state, pool, nursery):

    with eliot.start_action(action_type="run_with_work") as action:
        worker = pool.get_process()

        nursery.start_soon(
            functools.partial(
                delegate_task, data=data, state=state, worker=worker, action=action
            )
        )
        nursery.start_soon(replay_child_messages, worker)

        await worker.wait()
        pool.add_new_process()


@log.log_call
async def process_stream(receiver, max_workers, should_log, module_names):

    state = {"modes": {"strict": True}}

    pool = Pool(max_workers, should_log=should_log, module_names=module_names)
    pool.start()

    async with trio.open_nursery() as nursery:
        async for message in receiver:
            with eliot.start_action(state=state):
                # Handle state changes.
                data = json.loads(message.decode())
                maybe_new_state = set_state(data, state)
                if maybe_new_state is not None:
                    state = maybe_new_state
                    continue

                # This logic could be moved into worker/plugin to allow for more modes.
                if not data["result"]["final"] and state["modes"]["strict"]:
                    continue
                if data["result"]["final"] and not state["modes"]["strict"]:
                    continue

                nursery.start_soon(
                    functools.partial(
                        run_worker, data=data, state=state, pool=pool, nursery=nursery
                    )
                )


@log.log_call
async def async_main(should_log, module_names: Optional[List[str]], max_workers=3):

    stream = trio._unix_pipes.PipeReceiveStream(os.dup(0))
    receiver = streaming.TerminatedFrameReceiver(stream, b"\n")

    default_module_names = None
    module_names = default_module_names

    await process_stream(
        receiver,
        max_workers=max_workers,
        should_log=should_log,
        module_names=module_names,
    )


@log.log_call
def main(should_log, module_names: Optional[List[str]]):
    trio.run(functools.partial(async_main, should_log, module_names))
