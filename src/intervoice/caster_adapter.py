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
        if await self.condition(arg):
            await self.action(arg)


@attr.dataclass
class AppContext:
    title: str
    executable: str


@attr.dataclass
class Dictation:
    name: str


@attr.dataclass
class IntegerRefST:
    name: str
    start: int
    end: int


@attr.dataclass
class RepeatedAction:
    action: AsyncActionType
    extra: str

    async def execute(self, arg=None):
        times = arg[self.extra]
        for _ in range(times):
            await self.action.execute()


@attr.dataclass
class Choice:
    name: str
    mapping: dict


@attr.dataclass
class Repeat:
    extra: str

    def __rmul__(self, action):
        return RepeatedAction(action, self.extra)


@attr.dataclass
class FunctionAction:
    callable: types.FunctionType
    positional_arguments: tuple
    keyword_arguments: dict

    async def execute(self, arg):
        return self.callable(*self.positional_arguments, **self.keyword_arguments)


def add_to_registry(mapping, registry):
    # TODO don't mutate registry
    for pattern, action in mapping.items():
        registry.register(utils.quote(pattern))(action.execute)

    return registry


def _function(f, **kwargs):
    return FunctionAction(f, positional_arguments=(), keyword_arguments=kwargs)


class MergeRule:
    pass


class CCRMerger:
    CORE = 1


@attr.dataclass
class Grammar:
    name: str
    context: AppContext


class Settings:
    def __getitem__(self, name):
        return Settings()

    def __bool__(self):
        return False


R = RegisteredAction
Text = lambda x: ActionSequence([TextAction(x)])
Key = lambda x: ActionSequence([KeyAction(x)])
Function = _function
settings = types.SimpleNamespace(SETTINGS=Settings())
control = None
