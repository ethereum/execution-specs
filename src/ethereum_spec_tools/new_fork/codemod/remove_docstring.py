"""
libcst codemod that removes the module docstring.
"""

import libcst as cst
from libcst.codemod import CodemodCommand
from typing_extensions import override


class RemoveDocstringCommand(CodemodCommand):
    """
    Removes the module docstring if it exists.
    """

    DESCRIPTION: str = "Remove the module docstring."

    @override
    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        """
        Transform the tree by removing the docstring.
        """
        if len(tree.body) == 0:
            return tree
        first_stmt = tree.body[0]
        if not isinstance(first_stmt, cst.SimpleStatementLine):
            return tree
        if len(first_stmt.body) != 1:
            return tree
        expr = first_stmt.body[0]
        if not isinstance(expr, cst.Expr):
            return tree
        if not isinstance(expr.value, cst.SimpleString):
            return tree
        new_body = tree.body[1:]
        return tree.with_changes(body=new_body)
