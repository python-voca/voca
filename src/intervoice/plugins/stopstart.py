import sys

from intervoice import utils


registry = utils.Registry()


@registry.register('"start"')
async def _start(message):
    sys.exit(3)
