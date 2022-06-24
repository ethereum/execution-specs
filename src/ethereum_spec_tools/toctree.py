"""
Modify toctree
^^^^^^^^^^^^^^

Plug-in that modifies/re-orders the toc-tree before writing.
"""

from typing import Any

from ethereum_spec_tools.forks import Hardfork

forks = Hardfork.discover()


def modify_toctree(
    app: Any, what: Any, name: Any, obj: Any, skip: Any, options: Any
) -> None:
    """
    Autoapi is mapping some constants with similar names to the same TOC entry.
    """
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


def setup(sphinx: Any) -> None:
    """
    Update documentation structure before writing the files
    """
    sphinx.connect("autoapi-skip-member", modify_toctree)
