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
Plugin for working with files.
"""

import shutil
from io import TextIOBase
from pathlib import Path, PurePath
from typing import Dict, Final, FrozenSet, Iterator, Sequence, Set, Tuple

from docc.build import Builder
from docc.context import Context
from docc.discover import Discover, T
from docc.document import Document, Node, OutputNode
from docc.settings import PluginSettings
from docc.source import Source


class FileSource(Source):
    """
    A Source representing a file.
    """

    _relative_path: Final[PurePath]
    absolute_path: Final[PurePath]

    def __init__(
        self, relative_path: PurePath, absolute_path: PurePath
    ) -> None:
        self._relative_path = relative_path
        self.absolute_path = absolute_path

    @property
    def relative_path(self) -> PurePath:
        """
        Location of this source, relative to the project root.
        """
        return self._relative_path

    @property
    def output_path(self) -> PurePath:
        """
        Where the output of this source should end up.
        """
        return self.relative_path.with_suffix("")


class FileNode(OutputNode):
    """
    A node representing a file to be copied to the output directory.
    """

    path: Path

    def __init__(self, path: Path) -> None:
        self.path = path

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
        return self.path.suffix

    def output(self, context: Context, destination: TextIOBase) -> None:
        """
        Write this Node to destination.
        """
        with self.path.open("r") as f:
            shutil.copyfileobj(f, destination)


class FilesBuilder(Builder):
    """
    Collect file sources and prepare them for reading.
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
        source_set = set(s for s in unprocessed if isinstance(s, FileSource))
        unprocessed -= source_set

        for source in source_set:
            processed[source] = Document(
                FileNode(Path(source.absolute_path)),
            )


class FilesDiscover(Discover):
    """
    Create sources for static files.
    """

    sources: Sequence[FileSource]

    def __init__(self, config: PluginSettings) -> None:
        """
        Construct a new instance with the given configuration.
        """
        files = config.get("files")
        if files is None:
            self.sources = []
        else:
            sources = []

            for item in files:
                absolute_path = config.resolve_path(PurePath(item))
                relative_path = config.unresolve_path(absolute_path)
                sources.append(FileSource(relative_path, absolute_path))

            self.sources = sources

    def discover(self, known: FrozenSet[T]) -> Iterator[Source]:
        """
        Find sources.
        """
        return iter(self.sources)
