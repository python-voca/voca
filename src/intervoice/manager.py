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


from voca import plugins
from voca import utils
from voca import streaming
from voca import log


def worker_cli(should_log, module_names: Optional[List[str]] = None) -> List[str]:
    if module_names is None:
        module_names = utils.plugin_module_paths()

    log_arg = "--log" if should_log else "--no-log"
    prefix = [sys.executable, "-m", "voca", log_arg, "worker"]
    command = prefix.copy()
    for module_name in module_names:
        command += ["-i", module_name]
    return command


@log.log_async_call
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


@log.log_async_call
async def delegate_task(data, worker, state, action):
    wrapped_data = dict(
        **data, state=state, eliot_task_id=action.serialize_task_id().decode()
    )
    await worker.stdin.send_all(json.dumps(wrapped_data).encode() + b"\n")


@attr.s
class Pool:
    num_workers: int = attr.ib(default=1)
    should_log: bool = attr.ib(default=True)
    module_names: list = attr.ib(factory=list)
    processes: set = attr.ib(factory=set)

    def start(self):
        for _ in range(self.num_workers):
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


@log.log_async_call
async def run_worker(data, state, pool):

    with eliot.start_action(action_type="run_with_work") as action:
        worker = pool.get_process()

        await delegate_task(data=data, state=state, worker=worker, action=action)
        await replay_child_messages(worker)

        await worker.wait()
        pool.add_new_process()


@log.log_async_call
async def process_stream(receiver, num_workers, should_log, module_names):

    state = {"modes": {"strict": True}}

    pool = Pool(num_workers, should_log=should_log, module_names=module_names)
    pool.start()

    async for message_bytes in receiver:
        message = message_bytes.decode()
        with eliot.start_action(state=state):
            data = json.loads(message)
            if "result" not in data.keys():
                # Received a log, not a command.
                print(message)
                continue
            # Handle state changes.
            maybe_new_state = set_state(data, state)
            if maybe_new_state is not None:
                state = maybe_new_state
                continue

            # This logic could be moved into worker/plugin to allow for more modes.
            if not data["result"]["final"] and state["modes"]["strict"]:
                continue
            if data["result"]["final"] and not state["modes"]["strict"]:
                continue

            await run_worker(data=data, state=state, pool=pool)


@log.log_async_call
async def async_main(should_log, module_names: Optional[List[str]], num_workers: int):

    stream = trio._unix_pipes.PipeReceiveStream(os.dup(0))
    receiver = streaming.TerminatedFrameReceiver(stream, b"\n")

    await process_stream(
        receiver,
        num_workers=num_workers,
        should_log=should_log,
        module_names=module_names,
    )


@log.log_call
def main(should_log, module_names: Optional[List[str]], num_workers: int):
    trio.run(functools.partial(async_main, should_log, module_names, num_workers))
