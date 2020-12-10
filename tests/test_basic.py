from textwrap import dedent

import sort_all


def test_sort_onliner_tuple() -> None:
    txt = dedent(
        """\
        from mod import name1, name2

        __all__ = ("name2", "name1")
    """
    )

    expected = dedent(
        """\
        from mod import name1, name2

        __all__ = ("name1", "name2")
    """
    )

    assert expected == sort_all._fix_src(txt, "<input>")


def test_sort_onliner_list() -> None:
    txt = dedent(
        """\
        from mod import name1, name2

        __all__ = ["name2", "name1"]
    """
    )

    expected = dedent(
        """\
        from mod import name1, name2

        __all__ = ["name1", "name2"]
    """
    )

    assert expected == sort_all._fix_src(txt, "<input>")


def test_sort_onliner_set() -> None:
    txt = dedent(
        """\
        from mod import name1, name2

        __all__ = {"name2", "name1"}
    """
    )

    expected = dedent(
        """\
        from mod import name1, name2

        __all__ = {"name1", "name2"}
    """
    )

    assert expected == sort_all._fix_src(txt, "<input>")


def test_sort_multiline_tuple() -> None:
    txt = dedent(
        """\
        from mod import name1, name2

        __all__ = (
            "name2",
            "name1",
        )
    """
    )

    expected = dedent(
        """\
        from mod import name1, name2

        __all__ = (
            "name1",
            "name2",
        )
    """
    )

    assert expected == sort_all._fix_src(txt, "<input>")


def test_sort_multiline_list() -> None:
    txt = dedent(
        """\
        from mod import name1, name2

        __all__ = [
            "name2",
            "name1",
        ]
    """
    )

    expected = dedent(
        """\
        from mod import name1, name2

        __all__ = [
            "name1",
            "name2",
        ]
    """
    )

    assert expected == sort_all._fix_src(txt, "<input>")


def test_sort_multiline_set() -> None:
    txt = dedent(
        """\
        from mod import name1, name2

        __all__ = {
            "name2",
            "name1",
        }
    """
    )

    expected = dedent(
        """\
        from mod import name1, name2

        __all__ = {
            "name1",
            "name2",
        }
    """
    )

    assert expected == sort_all._fix_src(txt, "<input>")


def test_sort_skip_nonconst() -> None:
    txt = dedent(
        """\
        from mod import name1, name2

        __all__ = (name2, name1)
    """
    )

    expected = dedent(
        """\
        from mod import name1, name2

        __all__ = (name2, name1)
    """
    )

    assert expected == sort_all._fix_src(txt, "<input>")


def test_sort_skip_non_list_set_tuple() -> None:
    txt = dedent(
        """\
        from mod import name1, name2

        __all__ = ['name1'] + ['name2']
    """
    )

    expected = dedent(
        """\
        from mod import name1, name2

        __all__ = ['name1'] + ['name2']
    """
    )

    assert expected == sort_all._fix_src(txt, "<input>")


def test_sort_skip_non_unknown_type() -> None:
    txt = dedent(
        """\
        from mod import name1, name2

        __all__ = 123
    """
    )

    expected = dedent(
        """\
        from mod import name1, name2

        __all__ = 123
    """
    )

    assert expected == sort_all._fix_src(txt, "<input>")


def test_skip_multiple_all() -> None:
    txt = dedent(
        """\
        from mod import name1, name2

        __all__ = ("name1")
        __all__ = ("name2")
    """
    )

    expected = dedent(
        """\
        from mod import name1, name2

        __all__ = ("name1")
        __all__ = ("name2")
    """
    )

    assert expected == sort_all._fix_src(txt, "<input>")


def test_sort_ann_assign_simple() -> None:
    txt = dedent(
        """\
        from typing import Tuple
        from mod import name1, name2

        __all__: Tuple[str, ...]
        __all__ = ("name2", "name1")
    """
    )

    expected = dedent(
        """\
        from typing import Tuple
        from mod import name1, name2

        __all__: Tuple[str, ...]
        __all__ = ("name1", "name2")
    """
    )

    assert expected == sort_all._fix_src(txt, "<input>")


def test_sort_ann_assign_real() -> None:
    txt = dedent(
        """\
        from typing import Tuple
        from mod import name1, name2

        __all__: Tuple[str, ...] = ('name2', 'name1')
    """
    )

    expected = dedent(
        """\
        from typing import Tuple
        from mod import name1, name2

        __all__: Tuple[str, ...] = ("name1", "name2")
    """
    )

    assert expected == sort_all._fix_src(txt, "<input>")


def test_sort_aug_assign_real() -> None:
    txt = dedent(
        """\
        from mod import name1, name2

        __all__ = ('a', 'b')
        __all__ += ('name2', 'name1')
    """
    )

    expected = dedent(
        """\
        from mod import name1, name2

        __all__ = ("a", "b")
        __all__ += ("name1", "name2")
    """
    )

    assert expected == sort_all._fix_src(txt, "<input>")
