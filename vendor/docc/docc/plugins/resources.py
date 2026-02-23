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
Plugin for working with importlib resources.
"""

import shutil
from io import TextIOBase
from pathlib import PurePath
from typing import Dict, Set, Tuple, Type, TypeVar

from importlib_resources import files
from importlib_resources.abc import Traversable

from docc.build import Builder
from docc.context import Context
from docc.document import Document, Node, OutputNode
from docc.settings import PluginSettings
from docc.source import Source

R = TypeVar("R", bound="ResourceSource")


class ResourceSource(Source):
    """
    A Source representing an importlib file.
    """

    resource: Traversable
    _output_path: PurePath
    extension: str

    @classmethod
    def with_path(
        cls: Type[R], mod: str, input_path: PurePath, output_path: PurePath
    ) -> R:
        """
        Create a source for a resource `input_path`, relative to the Python
        module `mod`, to be output at `output_path`. Note that `output_path`
        should not have a file extension (or "suffix".)
        """
        return cls(
            files(mod) / input_path,
            output_path,
            "".join(input_path.suffixes),
        )

    def __init__(
        self, resource: Traversable, output_path: PurePath, extension: str
    ) -> None:
        self._output_path = output_path
        self.resource = resource
        self.extension = extension

    @property
    def relative_path(self) -> None:
        """
        Path relative to the project root.
        """
        return None

    @property
    def output_path(self) -> PurePath:
        """
        Where to write the output from this Source relative to the output path.
        """
        return self._output_path


class ResourceNode(OutputNode):
    """
    A node representing an `importlib` resource, to be copied to the output
    directory.
    """

    _extension: str
    resource: Traversable

    def __init__(self, resource: Traversable, extension: str) -> None:
        self.resource = resource
        self._extension = extension

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old node with the given new node.
        """
        raise TypeError

    @property
    def children(self) -> Tuple[()]:
        """
        Child nodes belonging to this node.
        """
        return tuple()

    @property
    def extension(self) -> str:
        """
        The preferred file extension for this node.
        """
        return self._extension

    def output(self, context: Context, destination: TextIOBase) -> None:
        """
        Write this Node to destination.
        """
        with self.resource.open("r") as f:
            shutil.copyfileobj(f, destination)


class ResourceBuilder(Builder):
    """
    Collect resource sources and open them for reading.
    """

    def __init__(self, config: PluginSettings) -> None:
        """
        Create a builder with the given configuration.
        """

    def build(
        self,
        unprocessed: Set[Source],
        processed: Dict[Source, Document],
    ) -> None:
        """
        Consume unprocessed Sources and insert their Documents into processed.
        """
        source_set = set(
            s for s in unprocessed if isinstance(s, ResourceSource)
        )
        unprocessed -= source_set

        for source in source_set:
            processed[source] = Document(
                ResourceNode(source.resource, source.extension),
            )
