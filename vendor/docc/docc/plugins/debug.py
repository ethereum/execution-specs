# Copyright (C) 2023 Ethereum Foundation
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
Plugin for dumping the node tree to text files.
"""

from io import TextIOBase
from typing import Iterable

from docc.context import Context
from docc.document import Document, Node, OutputNode
from docc.settings import PluginSettings
from docc.transform import Transform


class DebugNode(OutputNode):
    """
    An `OuputNode` that renders its contents as a tree.
    """

    child: Node

    def __init__(self, child: Node) -> None:
        self.child = child

    @property
    def children(self) -> Iterable[Node]:
        """
        Child nodes belonging to this node.
        """
        return (self.child,)

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old node with the given new node.
        """
        if old == self.child:
            self.child = new

    def output(self, context: Context, destination: TextIOBase) -> None:
        """
        Attempt to write this node to destination.
        """
        self.dump(destination)  # pyre-ignore[6]

    @property
    def extension(self) -> str:
        """
        The preferred file extension for this node.
        """
        return ".txt"


class DebugTransform(Transform):
    """
    A plugin that renders to a human-readable format.
    """

    def __init__(self, settings: PluginSettings) -> None:
        pass

    def transform(self, context: Context) -> None:
        """
        Apply the transformation to the given document.
        """
        document = context[Document]
        document.root = DebugNode(document.root)
