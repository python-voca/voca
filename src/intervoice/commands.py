class Registry:
    def __init__(self, mapping=None):
        self.mapping = mapping or {}

    def register(self, function):
        self.mapping[function.__name__] = function
        return function


registry = Registry()


@registry.register
async def say(message):
    await run_subprocess(["notify-send", *message])
