from __future__ import annotations

import contextlib
import sys
import types
import re

from typing import Optional
from typing import List
from typing_extensions import Protocol


import attr
import trio
import lark

import intervoice.plugins
from intervoice import utils
from intervoice import context
from intervoice import log


class LazyLoader:
    def __getattr__(self, name):
        from intervoice.plugins import basic
        return getattr(basic, name)

basic = LazyLoader()

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
        await basic.press(self.name)


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


# @attr.dataclass
# class AppContext:
#     title: str
#     executable: str


@attr.dataclass
class Dictation:
    name: str

    def make_definitions(self):
        return {self.name: r"/\w+/"}


@attr.dataclass
class IntegerRefST:
    name: str
    start: int
    end: int

    def make_definitions(self):

        return {
            self.name: "|".join(
                utils.quote(str(i)) for i in range(self.start, min(self.end, 30))
            )
        }


@attr.dataclass
class RepeatedAction:
    action: AsyncActionType
    extra: str

    async def execute(self, arg=None):
        times = arg[self.extra]
        for _ in range(times):
            await self.action.execute()


@attr.dataclass
class DelayAction:
    duration: float

    async def execute(self, arg=None):
        await trio.sleep(self.duration)


@attr.dataclass
class Choice:
    name: str
    mapping: dict

    def make_definitions(self):
        definitions = {k: utils.quote(v) for k, v in self.mapping.items()}
        definitions[self.name] = "|".join(definitions.keys())
        return definitions


@attr.dataclass
class Repeat:
    extra: str

    def __mul__(self, action):
        return RepeatedAction(action, self.extra)

    __rmul__ = __mul__


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


def convert_key_name(name):
    modifiers, _dash, simple = name.partition("-")
    modifier_map = {"c": "control", "a": "alt", "s": "shift", "w": "super"}
    new_modifiers = [utils.KeyModifier(modifier_map[m]) for m in modifiers]
    return utils.KeyChord(new_modifiers, simple)


class SpecTransformer(lark.Transformer):
    def name(self, args):
        return args[0]

    def literal_name(self, args):
        return utils.quote(args[0])

    def angled_name(self, args):
        return args[0]

    def optional_component(self, args):
        return f"[{args[0]}]"

    def phrase_component(self, args):
        return args[0]

    def component(self, args):
        return args[0]

    def spec(self, args):
        return args[0]

    def group(self, args):
        return "(" + " | ".join(args) + ")"



def convert_spec(spec):

    pattern = r"""

    ?start : spec
    spec : component+
    component : optional_component | phrase_component | group
    optional_component : "[" component "]"
    group : "(" component ("|" component)+ ")"
    phrase_component : angled_name | literal_name
    angled_name : "<" name ">"
    literal_name : /[\w ]+/
    name : /\w+/


    %import common.WS

    %ignore WS

    """

    parser = lark.Lark(pattern, debug=True, maybe_placeholders=True)
    tree = parser.parse(spec)
    result = "".join(SpecTransformer().transform(tree))
    if result.startswith("[") and result.endswith("]"):
        raise NotImplementedError("Buggy translator")
    return result


def adapt_AppContext(title=None, executable=None):
    return context.WindowContext(title=title)


def adapt_Dictation(text):
    return Dictation(text)


def adapt_Key(text):

    keys = [key.strip() for key in text.split(",")]
    actions = []
    for key in keys:
        name, _slash, delay = key.partition("/")
        actions.append(KeyAction(name))
        actions.append(DelayAction(delay))
    return ActionSequence(actions)


def find_merge_rule_classes(module):
    rules = []
    for obj in module.__dict__.values():

        if (
            isinstance(obj, type)
            and issubclass(obj, Placeholder)
            and obj is not Placeholder
        ):
            rules.append(obj)

    return rules


@attr.dataclass
class Patch:
    module: types.ModuleType
    name: str
    new: object


@contextlib.contextmanager
def monkeypatch(module, name, new):
    original = getattr(module, name)
    setattr(module, name, new)
    yield
    setattr(module, name, original)


def monkeypatch_each(patches):
    for patch in patches:
        monkeypatch(patch.module, patch.name, patch.new)

@log.log_call
def add_wrapper(module):
    rules = find_merge_rule_classes(module)

    registry = utils.Registry()

    for rule in rules:
        for spec, action in rule.mapping.items():
            try:

                converted_spec = convert_spec(spec)
            except (lark.exceptions.UnexpectedCharacters, NotImplementedError):
                converted_spec = '"aklsdjfkldjfk"'
            registry.register(converted_spec)(action.execute)
        for extra in rule.extras:
            registry.define(extra.make_definitions())

    # TODO use module.context
    wrapper = utils.Wrapper(registry, context=context.AlwaysContext())
    module.wrapper = wrapper


def patch_all():
    for module_path in paths_to_patch:
        sys.modules[module_path] = namespace

    # XXX Maybe replace this with an import hook.
    utils.MODULE_TRANSFORMERS.append(add_wrapper)


class AttributeHaver:
    def __getattr__(self, name):
        return AttributeHaver()


class Placeholder:
    pass


paths_to_patch = [
    "dragonfly",
    "castervoice.lib",
    "castervoice.lib.actions",
    "castervoice.lib.context",
    "castervoice.lib.dfplus.additions",
    "castervoice.lib.dfplus.merge",
    "castervoice.lib.dfplus.merge.mergerule",
    "castervoice.lib.dfplus.state",
    "castervoice.lib.dfplus.state.short",
    "castervoice.lib.dfplus.merge.ccrmerger",
]


namespace = types.SimpleNamespace(
    R=RegisteredAction,
    Text=lambda x: ActionSequence([TextAction(x)]),
    Key=lambda x: ActionSequence([KeyAction(x)]),
    Function=_function,
    settings=types.SimpleNamespace(SETTINGS=Settings()),
    control=None,
    gfilter=None,
    AppContext=adapt_AppContext,
    Dictation=adapt_Dictation,
    Grammar=Grammar,
    Context=None,
    Repeat=Repeat,
    Choice=Choice,
    Mouse=None,
    Pause=None,
    IntegerRefST=IntegerRefST,
    MergeRule=Placeholder,
    CCRMerger=AttributeHaver(),
)
