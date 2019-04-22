import types

from typing import Optional
from typing import List
from typing_extensions import Protocol

import attr


from intervoice import utils
from intervoice.plugins import basic


class AsyncActionType(Protocol):
    async def execute(self, arg=None) -> None:
        ...


@attr.dataclass
class TextAction:
    text: str

    async def execute(self, arg=None) -> None:
        await basic.write(self.text.format_map(arg))


@attr.dataclass
class KeyAction:
    name: str

    async def execute(self, arg=None):
        await utils.press(self.name)


@attr.dataclass
class RegisteredAction:
    instruction: AsyncActionType = attr.ib()
    rdescript: Optional[str] = attr.ib(default=None)

    async def execute(self, arg=None) -> None:
        await self.instruction.execute(arg)


@attr.dataclass
class ActionSequence:
    actions: List[AsyncActionType]

    def __add__(self, other):
        return attr.evolve(self, actions=self.actions + other.actions)

    async def execute(self, arg=None):

        for action in self.actions:
            await action.execute(arg)


@attr.dataclass
class ConditionalAction:
    condition: types.FunctionType
    action: RegisteredAction

    async def execute(self, arg=None):
        if await condition(arg):
            await self.action(arg)


@attr.dataclass
class AppContext:
    executable: str


@attr.dataclass
class Dictation:
    name: str


@attr.dataclass
class IntegerRefST:
    name: str
    start: int
    end: int


def add_to_registry(mapping, registry):
    # TODO don't mutate registry
    for pattern, action in mapping.items():
        registry.register(utils.quote(pattern))(action.execute)

    return registry


R = RegisteredAction
Text = lambda x: ActionSequence([TextAction(x)])
Key = lambda x: ActionSequence([KeyAction(x)])
