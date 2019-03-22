import functools
import os
import itertools
import sys
import pathlib
import subprocess

import trio
import eliot

from intervoice import utils
from intervoice import plugins
from intervoice import streaming
from intervoice import log


def find_modules():
    modules = []
    for path in (pathlib.Path(__file__).parent / "plugins").iterdir():
        if not path.name.endswith("__init__.py"):
            module = "intervoice.plugins." + path.name.split(".")[0]
            modules.append(module)
    return modules


@log.log_call
async def make_worker(import_paths, socket_path, task_status=trio.TASK_STATUS_IGNORED):
    options = []
    for path in import_paths:
        options += ["-i", path]
    command = [sys.executable, "-m", "intervoice", "worker", *options, socket_path]
    while True:
        try:
            await utils.run_subprocess(command)
        except subprocess.CalledProcessError as e:
            if e.returncode == 3:
                eliot.Message.log(
                    message_type="restarting_worker", socket_path=socket_path
                )
            else:
                raise


@log.log_call
async def make_pool(nursery, import_paths, socket_paths):
    for socket_path in socket_paths:
        nursery.start_soon(make_worker, import_paths, socket_path)


@log.log_call
async def delegate_stream(stream):
    receiver = streaming.TerminatedFrameReceiver(stream, b"\n")
    socket_paths = [f"/tmp/intervoice/{i}" for i in range(3)]
    async with trio.open_nursery() as nursery:
        await make_pool(nursery, find_modules(), socket_paths)
        await trio.sleep(2)
        worker_socket = await trio.open_unix_socket(socket_paths[0])
        async for message in receiver:
            try:
                await worker_socket.send_all(message + b"\n")
            except trio.BrokenResourceError:
                await trio.sleep(1)
                worker_socket = await trio.open_unix_socket(socket_paths[0])
                await worker_socket.send_all(message + b"\n")


@log.log_call
async def async_main(path):
    await streaming.serve_unix_domain(handler=delegate_stream, path=path)


@log.log_call
def main(path):
    trio.run(functools.partial(async_main, path=path))
