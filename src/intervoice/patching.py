from __future__ import annotations

import contextlib
import collections
import sys
import types
import importlib
import importlib.machinery

from typing import Optional
from typing import Dict
from typing import List

import attr
import pytest


@attr.s(auto_attribs=True)
class PathLoader:
    namespace: dict
    fullname: str
    path: str
    target: types.ModuleType

    def create_module(self, spec: importlib.machinery.ModuleSpec):
        module = types.ModuleType(spec.name)
        module.__dict__.update(self.namespace)

        return module

    def exec_module(self, module):
        pass


class PathFinder:
    def __init__(self, modules, mapping):

        self.modules_to_handle = modules
        self.fullname_to_vars = mapping

    def find_spec(
        self, fullname: str, path: Optional[str], target=Optional[types.ModuleType]
    ):

        if not fullname in self.modules_to_handle:
            return None
        return Spec(
            name=fullname,
            loader=PathLoader(
                self.fullname_to_vars.get(fullname, {}), fullname, path, target
            ),
        )


@attr.s
class Spec:
    name = attr.ib()
    loader = attr.ib()
    submodule_search_locations = attr.ib(factory=list)
    has_location = attr.ib(default=True)
    cached = attr.ib(default=False)
    origin = attr.ib(default=None)


def ancestors(items):
    for i, item in enumerate(reversed(items), start=1):
        yield item, items[:-i]


def get_package_map(strings):
    m = collections.defaultdict(list)
    for string in strings:
        items = string.split(".")
        for module_name, parents in ancestors(items):
            for _parent in parents:
                package_name = ".".join(parents)
                module_full_name = package_name + "." + module_name
                if module_full_name not in m[package_name]:
                    m[package_name].append(module_full_name)

    return dict(m)


def make_finder(mapping):
    package_map = get_package_map(mapping.keys())
    allowed_names = []
    for lst in package_map.values():
        for sub in lst:
            allowed_names.append(sub)

    allowed_names += list(package_map.keys())
    return PathFinder(allowed_names, mapping)


@contextlib.contextmanager
def finder_patch(finder):
    sys.meta_path.insert(0, finder)
    yield
    sys.meta_path.remove(finder)


def test_get_package_map():
    modules = ["a.b", "a.b.c", "a.b.d", "a.b.c.e", "g.h.i.j"]
    expected = {
        "a": ["a.b"],
        "a.b": ["a.b.c", "a.b.d"],
        "a.b.c": ["a.b.c.e"],
        "g": ["g.h"],
        "g.h": ["g.h.i"],
        "g.h.i": ["g.h.i.j"],
    }
    assert get_package_map(modules) == expected
