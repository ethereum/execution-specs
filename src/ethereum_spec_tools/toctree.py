"""
Modify toctree
^^^^^^^^^^^^^^

Plug-in that modifies/re-orders the toc-tree before writing.
"""

from typing import Any

import ethereum
from ethereum_spec_tools.forks import Hardfork

forks = Hardfork.discover()


def modify_toctree(
    app: Any, what: Any, name: Any, obj: Any, skip: Any, options: Any
) -> bool:
    """
    The function can be used to modify the toctree in any way.
    Currently handles the following modifications
    1. Re-order the packages in the order of the hardforks
    2. Change the visibility of any items that are marked as autoapi_noshow
    """
    # Re-order the packages in the order of the hardforks
    if what == "package" and name == "ethereum":

        fork_name_list = [x.name for x in forks]
        ordered_list = [None] * len(obj.subpackages)
        non_fork_package_index = len(fork_name_list)
        for package in obj.subpackages:
            try:
                package_index = fork_name_list.index(package.name)
            except ValueError:
                package_index = non_fork_package_index
                non_fork_package_index += 1

            ordered_list[package_index] = package

        obj.subpackages = ordered_list

    # Change the visibility of any items that are marked for no show
    if "autoapi_noshow" in obj._docstring:
        skip = True

    return skip


def setup(sphinx: Any) -> Any:
    """
    Update documentation structure before writing the files
    """
    sphinx.connect("autoapi-skip-member", modify_toctree)

    return {
        "version": ethereum.__version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
