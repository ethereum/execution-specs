"""
libcst codemod that updates the value of a constant.
"""

import argparse
from typing import ClassVar, Collection

import libcst as cst
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata import (
    FullyQualifiedNameProvider,
    ParentNodeProvider,
    QualifiedName,
)
from libcst.metadata.base_provider import ProviderT
from typing_extensions import override


class SetConstantCommand(VisitorBasedCodemodCommand):
    """
    Replaces the value of a constant identified by a fully qualified name.
    """

    DESCRIPTION: str = "Replace the value of a constant."
    METADATA_DEPENDENCIES: ClassVar[Collection[ProviderT]] = (
        FullyQualifiedNameProvider,
        ParentNodeProvider,
    )

    qualified_name: str
    value: cst.BaseExpression
    imports: list[list[str]]

    _in_assign_target: bool
    _matches: bool

    @staticmethod
    def add_args(arg_parser: argparse.ArgumentParser) -> None:
        """
        Add command-line args that a user can specify for running this codemod.
        """
        arg_parser.add_argument(
            "--qualified-name",
            "-n",
            dest="qualified_name",
            metavar="NAME",
            help="Qualified Python name, like ethereum.osaka.FORK_CRITERIA.",
            type=str,
            required=True,
        )
        arg_parser.add_argument(
            "--value",
            dest="value",
            metavar="VALUE",
            help="Replacement value to assign to the qualified name.",
            type=str,
            required=True,
        )
        arg_parser.add_argument(
            "--import",
            dest="imports",
            metavar="FROM IDENT",
            action="append",
            nargs=2,
            help="Additional imports to add to the module.",
        )

    def __init__(
        self,
        context: CodemodContext,
        qualified_name: str,
        value: str,
        imports: list[list[str]] | None,
    ) -> None:
        super().__init__(context)
        self.qualified_name = qualified_name
        self.value = cst.parse_expression(value)
        self._in_assign_target = False
        self._matches = False
        self.imports = imports or []

    @override
    def visit_Assign_targets(self, node: cst.Assign) -> None:  # noqa: D102
        if self._in_assign_target:
            raise Exception("already in assign target")
        self._in_assign_target = True

    @override
    def leave_Assign_targets(self, node: cst.Assign) -> None:  # noqa: D102
        if not self._in_assign_target:
            raise Exception("not in assign target")
        self._in_assign_target = False

    @override
    def visit_Assign(self, node: cst.Assign) -> None:  # noqa: D102
        if self._matches or self._in_assign_target:
            raise Exception("nested assign")

    @override
    def leave_Assign(  # noqa: D102
        self, original_node: cst.Assign, updated_node: cst.Assign
    ) -> cst.Assign:
        if self._in_assign_target:
            raise Exception("still in assign target")

        if not self._matches:
            return updated_node

        self._matches = False

        if len(original_node.targets) != 1:
            raise NotImplementedError(
                "cannot set value of unpacking assignment"
            )

        for module, identifier in self.imports:
            AddImportsVisitor.add_needed_import(
                self.context, module, identifier
            )
            RemoveImportsVisitor.remove_unused_import(
                self.context, module, identifier
            )

        return updated_node.with_changes(value=self.value.deep_clone())

    @override
    def visit_Name(self, node: cst.Name) -> None:  # noqa: D102
        if not self._in_assign_target:
            return

        qualified_names = self.get_metadata(FullyQualifiedNameProvider, node)
        if not qualified_names:
            return

        for qualified_name in qualified_names:
            assert isinstance(qualified_name, QualifiedName)

            if qualified_name.name == self.qualified_name:
                self._matches = True
                break
