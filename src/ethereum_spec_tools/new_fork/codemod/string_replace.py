"""
libcst codemod that replaces text within strings.
"""

import argparse
import dataclasses
from typing import Sequence

import libcst as cst
from libcst import matchers as m
from libcst.codemod import CodemodCommand, CodemodContext
from typing_extensions import override


class StringReplaceCommand(CodemodCommand):
    """
    Replaces text within strings.
    """

    DESCRIPTION: str = "Replace text within strings."

    replacements: list[tuple[(str, str)]]

    @staticmethod
    def add_args(arg_parser: argparse.ArgumentParser) -> None:
        """
        Add command-line args that a user can specify for running this codemod.
        """
        arg_parser.add_argument(
            "--replace",
            "-r",
            dest="replacements",
            metavar="OLD NEW",
            action="append",
            nargs=2,
            help="Text replacement to perform.",
            required=True,
        )

    def __init__(
        self,
        context: CodemodContext,
        replacements: list[list[str]] | None,
    ) -> None:
        super().__init__(context)
        if replacements is None:
            replacements = []
        self.replacements = [(a, b) for a, b in replacements]

    @override
    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        """
        Transform the tree.
        """
        result = m.replace(
            tree,
            m.SimpleString(),
            # `isfunction` returns `False` for bound methods...
            lambda a, b: self._replacement(a, b),
        )
        assert isinstance(result, cst.Module)
        return result

    def _replacement(
        self,
        node: cst.CSTNode,
        extracted: dict[str, cst.CSTNode | Sequence[cst.CSTNode]],
    ) -> cst.CSTNode:
        del extracted
        assert isinstance(node, cst.SimpleString)

        value = node.value
        for old, new in self.replacements:
            value = value.replace(old, new)

        if value == node.value:
            return node

        return dataclasses.replace(node, value=value)
