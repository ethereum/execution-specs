import ast
from textwrap import dedent

from ethereum_spec_tools.lint import Diagnostic
from ethereum_spec_tools.lint.lints.patch_hygiene import PatchHygiene
from ethereum_spec_tools.lint.lints.patch_hygiene import (
    _Visitor as PatchHygieneVisitor,
)


def test_visitor_assignment_simple() -> None:
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
    src = """
    (variable0, variable1) = (67, 68)
    """
    tree = ast.parse(dedent(src))
    visitor = PatchHygieneVisitor()
    visitor.visit(tree)
    items = visitor.items
    assert items == ["variable0", "variable1"]


def test_visitor_class() -> None:
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
    old = None
    new = ""

    lint = PatchHygiene()
    diagnostics = lint.compare("new_module", new, old)
    assert diagnostics == []


def test_patch_hygiene_compare_both_empty() -> None:
    old = ""
    new = ""

    lint = PatchHygiene()
    diagnostics = lint.compare("empty", new, old)
    assert diagnostics == []


def test_patch_hygiene_compare_add_new_assign() -> None:
    old = ""
    new = "SOME_CONSTANT = 3"

    lint = PatchHygiene()
    diagnostics = lint.compare("new_assign", new, old)
    assert diagnostics == []


def test_patch_hygiene_compare_remove_assign() -> None:
    old = "SOME_CONSTANT = 3"
    new = ""

    lint = PatchHygiene()
    diagnostics = lint.compare("remove_assign", new, old)
    assert diagnostics == []


def test_patch_hygiene_compare_reorder_assign() -> None:
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
