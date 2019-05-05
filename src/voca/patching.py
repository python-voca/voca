from __future__ import annotations

import contextlib
import collections
import sys
import types
import importlib
import importlib.machinery
import importlib.util

from typing import Generator
from typing import ContextManager
from typing import Optional
from typing import Dict
from typing import List
from typing import Any
from typing import DefaultDict
from typing import TypeVar


import attr

from voca import utils

T = TypeVar("T")


@attr.s(auto_attribs=True)
class PathLoader:
    namespace: dict
    fullname: str
    path: Optional[str]
    target: types.ModuleType

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> types.ModuleType:
        """Create a module with the name and namespace."""
        module = types.ModuleType(spec.name)
        module.__dict__.update(self.namespace)

        return module

    def exec_module(self, module):
        """No-op to match the Loader interface."""
        pass


@contextlib.contextmanager
def skipping_finder(finder: importlib.abc.MetaPathFinder) -> Generator:
    """Context manager for importing modules while excluding the ``finder`` from ``sys.meta_path``."""

    def placeholder_find_spec(_fullname, _path, _target):
        return None

    finder_placeholder = types.SimpleNamespace(find_spec=placeholder_find_spec)

    sys.meta_path[sys.meta_path.index(finder)] = finder_placeholder
    try:
        yield
    finally:
        sys.meta_path[sys.meta_path.index(finder_placeholder)] = finder


@contextlib.contextmanager
def skipping_module_in_sys_modules(module_name: star) -> Generator:
    """Context manager for importing modules while skipping any cached entry in ``sys.modules``."""
    # Use a sentinel to check if we need to restore parent module to sys.modules.
    sentinel = object()
    parent_module = sys.modules.pop(module_name, sentinel)
    try:
        yield
    finally:
        # Restore parent if necessary.
        if parent_module is not sentinel:

            # XXX Not sure if this is the right choice, or if it should leave
            # the existing entry in place.

            # Restore original module to sys.modules, bumping any entry created
            # during the `yield` above.
            sys.modules[module_name] = parent_module


@contextlib.contextmanager
def finder_patch(finder: importlib.abc.MetaPathFinder) -> Generator:
    """Context manager for importing modules with ``finder`` on ``sys.meta_path``."""
    sys.meta_path.insert(0, finder)
    try:
        yield
    finally:
        sys.meta_path.remove(finder)


@attr.s(auto_attribs=True)
class PathFinder:
    modules_to_handle: List[str]
    fullname_to_vars: Dict[str, Dict[str, Any]]

    def find_spec(
        self, fullname: str, path: Optional[str], target=Optional[types.ModuleType]
    ) -> Spec:
        """Build a spec for modules in ``self.modules_to_handle``, behave normally otherwise."""
        if fullname not in self.modules_to_handle:
            # Return a spec using the default behavior ignoring sys.modules and
            # this finder.
            parent_name = ".".join(fullname.split(".")[:-1])

            with skipping_finder(self), skipping_module_in_sys_modules(parent_name):

                return importlib.util.find_spec(fullname, path)

        variables = self.fullname_to_vars.get(fullname, {})
        loader = PathLoader(variables, fullname, path, target)

        return Spec(name=fullname, loader=loader)


@attr.s
class Spec:
    name = attr.ib()
    loader = attr.ib()
    submodule_search_locations = attr.ib(factory=list)
    has_location = attr.ib(default=True)
    cached = attr.ib(default=False)
    origin = attr.ib(default=None)


def ancestors(items: List[T]) -> Generator[T, List[T], None]:
    for i, item in enumerate(reversed(items), start=1):
        yield item, items[:-i]


def get_package_map(strings: List[str]) -> Dict[str, List[str]]:
    """Return a dict mapping packages to the modules they contain."""
    m: DefaultDict[str, List[str]] = collections.defaultdict(list)
    for string in strings:
        items = string.split(".")
        for module_name, parents in ancestors(items):
            for _parent in parents:
                package_name = ".".join(parents)
                module_full_name = package_name + "." + module_name
                if module_full_name not in m[package_name]:
                    m[package_name].append(module_full_name)

    return dict(m)


@utils.public
def make_finder(mapping: Dict[str, Dict[str, Any]]) -> PathFinder:
    """Build a Finder that handles modules in ``mapping``."""
    package_map = get_package_map(mapping.keys())
    allowed_names = []
    for lst in package_map.values():
        for sub in lst:
            allowed_names.append(sub)

    allowed_names += list(package_map.keys())
    return PathFinder(allowed_names, mapping)
