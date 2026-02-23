# Copyright (C) 2022-2023 Ethereum Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Load plugins.
"""

import sys
from inspect import isabstract
from typing import Callable, Dict, Type, TypeVar

if sys.version_info < (3, 10):
    from importlib_metadata import EntryPoint, entry_points
else:
    from importlib.metadata import EntryPoint, entry_points


class PluginError(Exception):
    """
    An error encountered while loading a plugin.
    """


L = TypeVar("L")


class Loader:
    """
    Facilitates loading plugins.
    """

    entry_points: Dict[str, EntryPoint]

    def __init__(self) -> None:
        """
        Create an instance and populate it with the discovered plugins.
        """
        found = set(entry_points(group="docc.plugins"))
        self.entry_points = {entry.name: entry for entry in found}

    def load(self, base: Type[L], name: str) -> Callable[..., L]:
        """
        Load a plugin by name.
        """
        class_ = self.entry_points[name].load()

        if isabstract(class_):
            raise PluginError(f"type {class_} is abstract")

        if not issubclass(class_, base):
            raise PluginError(f"type {class_} is not a subclass of {base}")

        return class_
