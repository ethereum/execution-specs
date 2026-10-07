"""Tests for linting tools."""

import ast
from textwrap import dedent

import pytest

from ethereum_spec_tools.lint import Diagnostic
from ethereum_spec_tools.lint.lints.formatting_hygiene import FormattingHygiene
from ethereum_spec_tools.lint.lints.patch_hygiene import PatchHygiene
from ethereum_spec_tools.lint.lints.patch_hygiene import (
    _Visitor as PatchHygieneVisitor,
)


def test_visitor_assignment_simple() -> None:
    """
    Tests that the visitor correctly identifies simple variable
    assignments.
    """
    src = """
    variable0 = 67
    variable1 = 68
    """
    tree = ast.parse(dedent(src))
    visitor = PatchHygieneVisitor()
    visitor.visit(tree)
    items = visitor.items
    assert items == ["variable0", "variable1"]


def test_visitor_assignment_tuple() -> None:
    """
    Tests that the visitor correctly identifies tuple variable
    assignments.
    """
    src = """
    (variable0, variable1) = (67, 68)
    """
    tree = ast.parse(dedent(src))
    visitor = PatchHygieneVisitor()
    visitor.visit(tree)
    items = visitor.items
    assert items == ["variable0", "variable1"]


def test_visitor_class() -> None:
    """
    Tests that the visitor correctly identifies class definitions and
    their members.
    """
    src = """
    class Foo:
        some_field: int
        some_assignment = 3

        def some_function(self):
            invisible = 3
    """
    tree = ast.parse(dedent(src))
    visitor = PatchHygieneVisitor()
    visitor.visit(tree)
    items = visitor.items
    assert items == [
        "Foo",
        "Foo.some_field",
        "Foo.some_assignment",
        "Foo.some_function",
    ]


def test_visitor_class_nested() -> None:
    """Tests that the visitor correctly identifies nested class definitions."""
    src = """
    class Foo:
        class Bar:
            some_field = 4
    """
    tree = ast.parse(dedent(src))
    visitor = PatchHygieneVisitor()
    visitor.visit(tree)
    items = visitor.items
    assert items == [
        "Foo",
        "Foo.Bar",
        "Foo.Bar.some_field",
    ]


def test_patch_hygiene_compare_new_module() -> None:
    """Tests that patch hygiene allows creating new modules without issues."""
    old = None
    new = ""

    lint = PatchHygiene()
    diagnostics = lint.compare("new_module", new, old)
    assert diagnostics == []


def test_patch_hygiene_compare_both_empty() -> None:
    """Tests that patch hygiene handles empty modules correctly."""
    old = ""
    new = ""

    lint = PatchHygiene()
    diagnostics = lint.compare("empty", new, old)
    assert diagnostics == []


def test_patch_hygiene_compare_add_new_assign() -> None:
    """Tests that patch hygiene allows adding new assignments."""
    old = ""
    new = "SOME_CONSTANT = 3"

    lint = PatchHygiene()
    diagnostics = lint.compare("new_assign", new, old)
    assert diagnostics == []


def test_patch_hygiene_compare_remove_assign() -> None:
    """Tests that patch hygiene allows removing assignments."""
    old = "SOME_CONSTANT = 3"
    new = ""

    lint = PatchHygiene()
    diagnostics = lint.compare("remove_assign", new, old)
    assert diagnostics == []


def test_patch_hygiene_compare_reorder_assign() -> None:
    """Tests that patch hygiene detects when assignments are reordered."""
    old = """
    FIRST_CONSTANT = 3
    SECOND_CONSTANT = 3
    """

    new = """
    SECOND_CONSTANT = 3
    FIRST_CONSTANT = 3
    """

    lint = PatchHygiene()
    diagnostics = lint.compare("reorder_assign", dedent(new), dedent(old))
    assert diagnostics == [
        Diagnostic(
            message=(
                "the item `FIRST_CONSTANT` in `reorder_assign` has changed "
                "relative positions"
            )
        )
    ]


def test_patch_hygiene_compare_add_between_assign() -> None:
    """
    Tests that patch hygiene allows adding assignments between
    existing ones.
    """
    old = """
    FIRST_CONSTANT = 3
    SECOND_CONSTANT = 3
    """

    new = """
    FIRST_CONSTANT = 3
    NEW_CONSTANT = 3
    SECOND_CONSTANT = 3
    """

    lint = PatchHygiene()
    diagnostics = lint.compare("add_between_assign", dedent(new), dedent(old))
    assert diagnostics == []


def test_patch_hygiene_compare_reorder_between_assign() -> None:
    """
    Tests that patch hygiene detects reordering when new assignments are
    added between existing ones.
    """
    old = """
    FIRST_CONSTANT = 3
    SECOND_CONSTANT = 3
    """

    new = """
    SECOND_CONSTANT = 3
    NEW_CONSTANT = 3
    FIRST_CONSTANT = 3
    """

    lint = PatchHygiene()
    diagnostics = lint.compare(
        "reorder_between_assign", dedent(new), dedent(old)
    )
    assert diagnostics == [
        Diagnostic(
            message=(
                "the item `FIRST_CONSTANT` in `reorder_between_assign` has "
                "changed relative positions"
            )
        )
    ]


def test_formatting_hygiene_compare_new_module() -> None:
    """Tests that formatting hygiene allows creating new modules."""
    lint = FormattingHygiene()
    assert lint.compare("new_module", "x = 1\n", None, "parent") == []


def test_formatting_hygiene_compare_identical() -> None:
    """Tests that formatting hygiene accepts identical modules."""
    source = "def f(a, b):\n    return g(a, b)\n"

    lint = FormattingHygiene()
    assert lint.compare("identical", source, source, "parent") == []


@pytest.mark.parametrize(
    "old,new",
    [
        pytest.param(
            """
            x = g(
                aaaa, bbbb
            )
            """,
            """
            x = g(
                aaaa,
                bbbb,
            )
            """,
            id="call_exploded",
        ),
        pytest.param(
            """
            a = 1
            b = 2
            """,
            """
            a = 1

            b = 2
            """,
            id="blank_line_added",
        ),
        pytest.param(
            '''
            def f():
                """
                Check the gas limit against the
                parent block.
                """
            ''',
            '''
            def f():
                """
                Check the gas limit against the parent
                block.
                """
            ''',
            id="docstring_rewrapped",
        ),
    ],
)
def test_formatting_hygiene_compare_formatting_only(
    old: str, new: str
) -> None:
    """
    Tests that formatting hygiene reports changes that only reformat code.
    """
    lint = FormattingHygiene()
    diagnostics = lint.compare("module", dedent(new), dedent(old), "parent")
    assert len(diagnostics) == 1
    assert diagnostics[0].message.startswith("`module` line ")
    assert diagnostics[0].message.endswith(
        "differs from `parent` only in formatting"
    )


@pytest.mark.parametrize(
    "old,new",
    [
        pytest.param(
            """
            x = g(
                aaaa, bbbb
            )
            """,
            """
            x = g(
                aaaa,
                cccc,
            )
            """,
            id="argument_changed_and_exploded",
        ),
        pytest.param(
            """
            # Charge the base cost.
            charge_gas(evm, cost)
            """,
            """
            # Charge the base cost first.
            charge_gas(evm, cost)
            """,
            id="comment_reworded",
        ),
        pytest.param(
            """
            name = "a b"
            """,
            """
            name = "ab"
            """,
            id="string_spacing_changed",
        ),
        pytest.param(
            """
            for x in y:
                a(x)
                b(x)
            """,
            """
            for x in y:
                a(x)
            b(x)
            """,
            id="statement_moved_out_of_loop",
        ),
        pytest.param(
            """
            if flag:
                a()
            b()
            """,
            """
            if flag:
                a()
                b()
            """,
            id="statement_moved_into_block",
        ),
    ],
)
def test_formatting_hygiene_compare_real_change(old: str, new: str) -> None:
    """
    Tests that formatting hygiene allows changes to code or comments.
    """
    lint = FormattingHygiene()
    assert lint.compare("module", dedent(new), dedent(old), "parent") == []


def test_formatting_hygiene_compare_line_number() -> None:
    """
    Tests that formatting hygiene reports the line in the newer hardfork.
    """
    old = "a = 1\nb = g(x, y)\n"
    new = "a = 1\nb = g(\n    x,\n    y,\n)\n"

    lint = FormattingHygiene()
    assert lint.compare("module", new, old, "parent") == [
        Diagnostic(
            message="`module` line 2 differs from `parent` only in formatting"
        )
    ]
