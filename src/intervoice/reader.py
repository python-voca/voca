import functools
import os
import itertools

import trio

BUFSIZE = 2 ** 14
counter = itertools.count()


async def open_unix_domain_listeners(path, *, permissions=None):
    sock = trio.socket.socket(trio.socket.AF_UNIX, trio.socket.SOCK_STREAM)
    try:
        os.unlink(path)
    except OSError:
        pass
    await sock.bind(path)
    if permissions is not None:
        os.fchmod(sock.fileno(), permissions)
    sock.listen(100)
    return [trio.SocketListener(sock)]


async def serve_unix_domain(
    handler,
    path,
    *,
    permissions=None,
    handler_nursery=None,
    task_status=trio.TASK_STATUS_IGNORED,
):
    listeners = await open_unix_domain_listeners(path, permissions=permissions)
    await trio.serve_listeners(
        handler, listeners, handler_nursery=handler_nursery, task_status=task_status
    )


numbers = {
    word: integer
    for integer, word in enumerate(
        [
            "zero",
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
        ]
    )
}


async def sleep_for(i, length):
    print(i, "sleeping for", length)
    await trio.sleep(length)
    print(i, "woke up")


async def handle(stream):
    got_bytes = await stream.receive_some(BUFSIZE)
    got_text = got_bytes.decode().rstrip()
    got_lines = got_text.splitlines()
    print(got_lines)
    i = next(counter)

    try:
        number = numbers[got_text]
    except KeyError as e:
        print("err", e)
    else:
        await sleep_for(i, number)


async def async_main(path):
    await serve_unix_domain(handler=handle, path=path)


def main(path):
    trio.run(functools.partial(async_main, path=path))
