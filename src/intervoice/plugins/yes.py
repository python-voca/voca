from voca import utils
from voca import context
from voca.plugins import basic


registry = utils.Registry()
registry.define({"?text": r"/\w.+/"})


@registry.register('"hit" chord')
async def _say_def(message):
    await basic.write("def")


wrapper = utils.Wrapper(registry)
