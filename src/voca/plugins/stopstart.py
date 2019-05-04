import sys

from voca import utils


registry = utils.Registry()


@registry.register('"start"')
async def _start(message: str):
    sys.exit(3)


wrapper = utils.Wrapper(registry)
