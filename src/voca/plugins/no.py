from voca import utils
from voca import context
from voca.plugins import basic


registry = utils.Registry()
registry.define({"?text": r"/\w.+/"})


wrapper = utils.Wrapper(registry, context=context.NeverContext())


@registry.register('"nope"')
async def _say_xyz(message):
    await basic.write("xyz")


wrapper = utils.Wrapper(registry, context=context.NeverContext())
