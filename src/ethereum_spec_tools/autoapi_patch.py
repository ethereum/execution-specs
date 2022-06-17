"""
The autoapi function used for documentation does not
fully capture assignment of object variables.

E.g- in the module test.py
A.x = 10
B.x = 5

Both instances are treated as `test.x` instead of `test.A.x` & `test.B.x`
This could incorrectly lead to duplicates.

This tool is uased as a patch.
"""

from typing import Any

import astroid
from autoapi.mappers.python import astroid_utils


def get_assign_value_patch(node: Any) -> Any:
    """
    The get_assign_value function in autoapi.mappers.python.astroid_utils
    does not handle Attribute assignment properly in that it only considers the
    attribute name and omits out the information about the parent object
    """
    try:
        targets = node.targets
    except AttributeError:
        targets = [node.target]

    if len(targets) == 1:
        target = targets[0]
        name = get_assign_name(target)
        if name:
            return (name, astroid_utils._get_const_values(node.value))

    return None


def get_assign_name(target: Any) -> Any:
    """
    Recursively the assign name
    """
    if isinstance(target, astroid.nodes.AssignName) or isinstance(
        target, astroid.nodes.Name
    ):
        return target.name
    elif isinstance(target, astroid.nodes.AssignAttr) or isinstance(
        target, astroid.nodes.Attribute
    ):
        return get_assign_name(target.expr) + "." + target.attrname
    else:
        return None


def apply_patch() -> None:
    """
    Apply the patch
    """
    astroid_utils.get_assign_value = get_assign_value_patch
