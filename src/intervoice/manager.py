import functools
import os
import itertools
import sys
import pathlib
import subprocess
import json

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


@log.log_call
async def make_worker(import_paths, socket_path, task_status=trio.TASK_STATUS_IGNORED):
    options = []
    for path in import_paths:
        options += ["-i", path]

    original_command = [
        sys.executable,
        "-m",
        "intervoice",
        "worker",
        *options,
        socket_path,
    ]
    command = original_command
    while True:
        try:
            await utils.run_subprocess(command)
        except subprocess.CalledProcessError as e:
            if e.returncode == 3:
                eliot.Message.log(
                    message_type="restarting_worker",
                    socket_path=socket_path,
                    returncode=e.returncode,
                )
                command = original_command
            elif e.returncode == 4:
                eliot.Message.log(message_type="stop_voice")
                command = [
                    sys.executable,
                    "-m",
                    "intervoice",
                    "worker",
                    "-i",
                    "intervoice.plugins.stopstart",
                    socket_path,
                ]

            else:
                raise


@log.log_call
async def make_pool(nursery, import_paths, socket_paths):
    # TODO Use standard streams instead of unix domain sockets.
    for socket_path in socket_paths:
        nursery.start_soon(make_worker, import_paths, socket_path)


@log.log_call
async def delegate_stream(stream):
    receiver = streaming.TerminatedFrameReceiver(stream, b"\n")
    # TODO This is insecure. Use TemporaryDirectory.
    socket_paths = [f"/tmp/intervoice/{i}" for i in range(3)]
    async with trio.open_nursery() as nursery:
        await make_pool(nursery, find_modules(plugins), socket_paths)
        await trio.sleep(2)
        worker_socket = await trio.open_unix_socket(socket_paths[0])
        async for input_message in receiver:
            with eliot.start_action() as action:
                output_message = json.dumps(
                    {
                        "eliot_task_id": action.serialize_task_id().decode(),
                        "body": input_message.decode(),
                    }
                ).encode()
                try:
                    await worker_socket.send_all(output_message + b"\n")
                except trio.BrokenResourceError:
                    await trio.sleep(1)
                    worker_socket = await trio.open_unix_socket(socket_paths[0])
                    await worker_socket.send_all(output_message + b"\n")


@log.log_call
async def async_main(path):
    await streaming.serve_unix_domain(handler=delegate_stream, path=path)


@log.log_call
def main(path):
    trio.run(functools.partial(async_main, path=path))
