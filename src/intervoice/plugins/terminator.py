from voca import utils
from voca import context
from voca.plugins import basic

registry = utils.Registry()


registry.define({"?text": r"/\w.+/"})
registry.register("declare text")(basic._alert)


wrapper = utils.Wrapper(
    registry=registry, context=context.WindowContext(title="terminator")
)
