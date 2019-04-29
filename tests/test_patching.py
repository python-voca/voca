import pytest

from voca import patching

def test_patch():
    mapping = {
        "a.b.c": {"x": 1},
        "a.b.d": {"y": 2},
        "a.b": {"qq": 55},
        "g.h.i": {"x": 44},
        "g.h.j": {"x": 66},
    }

    finder = patching.make_finder(mapping)
    with patching.finder_patch(finder):
        import a.b.c
        import a.b.d
        import collections
        import g.h.i



    assert a.b.qq == 55
    assert a.b.c.x == 1
    assert a.b.d.y == 2
    assert collections.Counter("xyy")["y"] == 2
    assert g.h.i.x == 44

    with pytest.raises(ImportError):
        import g.h.j


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
    assert patching.get_package_map(modules) == expected
