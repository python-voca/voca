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

import voca.plugins
from voca import utils
from voca import context
from voca import log
from voca import patching


class LazyLoader:
    def __getattr__(self, name):
        from voca.plugins import basic

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
        mapping = utils.value_to_pronunciation()
        alternatives = [
            mapping.get(str(i)) for i in range(self.start, min(self.end, 20))
        ]
        return {self.name: "/" + "|".join(alternatives) + "/"}


@attr.dataclass
class RepeatedAction:
    action: AsyncActionType
    extra: str

    async def execute(self, arg=None):

        # self.extra should be the name of the extra, like 'n'
        # arg should be a mapping of values said
        times = int(arg[self.extra])
        for _ in range(times):
            await self.action.execute(arg)


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
class MyRepeat:
    extra: str

    def __mul__(self, action):
        return RepeatedAction(action, self.extra)

    def __rmul__(self, action):
        return self * action


@attr.dataclass
class FunctionAction:
    callable: types.FunctionType
    positional_arguments: tuple
    keyword_arguments: dict

    async def execute(self, arg):
        return self.callable(*self.positional_arguments, **self.keyword_arguments)


class CasterTransformer(lark.Transformer):
    def n(self, arg):
        pronunciation = "".join(arg[0])
        value = utils.pronunciation_to_value()[pronunciation]
        return {"n": int(value)}


def transform_tree(tree):
    if not tree:
        return tree
    result = CasterTransformer().transform(tree[0])
    return result


async def _run(action, data):
    result = transform_tree(data)
    await action.execute(result)


def add_to_registry(mapping, registry):
    # TODO don't mutate registry
    for pattern, action in mapping.items():
        registry.register(utils.quote(pattern))(lambda data: _run(action, data))

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


class SpecTransformer(lark.Transformer):
    def name(self, args):
        return "".join(args)

    def literal_name(self, args):
        return " " + utils.quote(args[0].strip()) + " "

    def angled_name(self, args):
        return args[0]

    def optional_component(self, args):
        return f"[{args[0]}]"

    def phrase_component(self, args):
        return args[0]

    def component(self, args):
        return args[0]

    def spec(self, args):
        return "".join(args).strip()

    def group(self, args):
        return "(" + "|".join(args) + ")"


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
    result = result.replace('""', "")
    # XXX
    # if result.startswith("[") and result.endswith("]"):
    #     raise NotImplementedError(result + ": Buggy translator")
    return result


def adapt_AppContext(title=None, executable=None):
    return context.WindowContext(title=title)


def adapt_Dictation(text):
    return Dictation(text)


def convert_key_name(name):
    modifiers, _dash, simple = name.rpartition("-")
    modifier_map = {"c": "ctrl_l", "a": "alt", "s": "shift", "w": "cmd"}
    key_map = {"pgup": "page_up", "pgdown": "page_down"}
    new_modifiers = [utils.KeyModifier(modifier_map[m]) for m in modifiers]
    return utils.KeyChord(new_modifiers, key_map.get(simple, simple))


def adapt_Key(text):

    keys = [key.strip() for key in text.split(",")]
    actions = []
    for key in keys:
        name, _slash, delay = key.partition("/")

        actions.append(KeyAction(convert_key_name(name)))
        if delay:
            actions.append(DelayAction(float(delay)))

    return ActionSequence(actions)


def adapt_Text(name):
    return ActionSequence([TextAction(name)])


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
    if getattr(module, "wrapper", False):
        return module

    rules = find_merge_rule_classes(module)

    registry = utils.Registry()

    for rule in rules:
        for spec, action in rule.mapping.items():
            try:

                converted_spec = convert_spec(spec)
            except (lark.exceptions.UnexpectedCharacters, NotImplementedError):
                # XXX
                converted_spec = '"aklsdjfkldjfk"'
            # TODO Make this easier to read.
            registry.register(converted_spec)(
                lambda data, action=action: _run(action, data)
            )
        for extra in rule.extras:
            registry.define(extra.make_definitions())

    # TODO use module.context
    wrapper = utils.Wrapper(registry, context=context.AlwaysContext())
    module.wrapper = wrapper
    # XXX Avoid mutate-and-return.
    return module


def patch_all():

    # XXX Should fix this to avoid having to actually import castervoice.
    # Currently sys.modules is used to find castervoice in order to find its submodules.
    import castervoice

    finder = patching.make_finder(module_mapping)
    sys.meta_path.insert(0, finder)

    # XXX Maybe replace this with an import hook.
    utils.MODULE_TRANSFORMERS.append(add_wrapper)


class AttributeHaver:
    def __getattr__(self, name):
        return AttributeHaver()


class Placeholder:
    pass


class VirtualModule:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class VirtualPackage:
    def __init__(self, path, contents):
        self.__path__ = path
        self.__dict__.update(contents)


module_mapping = {
    "dragonfly.__init__": {},
    "dragonfly": {
        "Grammar": Grammar,
        "Context": None,
        "AppContext": adapt_AppContext,
        "Dictation": adapt_Dictation,
        "Repeat": MyRepeat,
        "Function": _function,
        "Choice": Choice,
        "Mouse": None,
        "Pause": None,
    },
    # "castervoice.lib": {},
    "castervoice.lib.control": {},
    "castervoice.lib.utilities": {"simple_log": lambda: None},
    # "castervoice.apps": {},
    # "castervoice.apps.__init__": {},
    "castervoice.lib.settings": {"SETTINGS": Settings()},
    "castervoice.lib.actions": {"Key": adapt_Key, "Text": adapt_Text},
    "castervoice.lib.context": {"AppContext": adapt_AppContext},
    "castervoice.lib.dfplus.additions": {"IntegerRefST": IntegerRefST},
    "castervoice.lib.dfplus.merge": {"gfilter": None},
    "castervoice.lib.dfplus.merge.mergerule": {"MergeRule": Placeholder},
    "castervoice.lib.dfplus.state.short": {"R": RegisteredAction},
    "castervoice.lib.dfplus.merge.ccrmerger": {"CCRMerger": AttributeHaver()},
}
