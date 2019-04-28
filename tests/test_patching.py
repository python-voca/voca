import pytest

from intervoice import patching

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
