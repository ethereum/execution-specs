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
Plugin that renders directory listings.
"""

from abc import ABC, abstractmethod
from os.path import commonpath
from pathlib import PurePath
from typing import Dict, Final, FrozenSet, Iterator, Set, Tuple

from jinja2 import Environment, PackageLoader, select_autoescape

from docc.build import Builder
from docc.context import Context
from docc.discover import Discover, T
from docc.document import Document, Node
from docc.plugins import html
from docc.settings import PluginSettings
from docc.source import Source


class Listable(ABC):
    """
    Mixin to change visibility of a Source in a directory listing.
    """

    @property
    @abstractmethod
    def show_in_listing(self) -> bool:
        """
        `True` if this `Source` should be shown in directory listings.
        """
        raise NotImplementedError()


class ListingDiscover(Discover):
    """
    Creates listing sources for each directory.
    """

    def __init__(self, config: PluginSettings) -> None:
        pass

    def discover(self, known: FrozenSet[T]) -> Iterator["ListingSource"]:
        """
        Find sources.
        """
        listings = {}

        for source in known:
            path = source.relative_path
            if isinstance(source, Listable):
                if not source.show_in_listing:
                    continue
            elif not path:
                continue

            if not path:
                path = source.output_path

            for parent in path.parents:
                try:
                    listing = listings[parent]
                except KeyError:
                    listing = ListingSource(parent, parent / "index", set())
                    listings[parent] = listing
                    yield listing

                listing.sources.add(source)
                source = listing


class ListingSource(Source):
    """
    A synthetic source that describes the contents of a directory.
    """

    _relative_path: Final[PurePath]
    _output_path: Final[PurePath]
    sources: Final[Set[Source]]

    def __init__(
        self,
        relative_path: PurePath,
        output_path: PurePath,
        sources: Set[Source],
    ) -> None:
        self._relative_path = relative_path
        self.sources = sources
        self._output_path = output_path

    @property
    def output_path(self) -> PurePath:
        """
        Where to write the output from this Source relative to the output path.
        """
        return self._output_path

    @property
    def relative_path(self) -> PurePath:
        """
        Path to the Source (if one exists) relative to the project root.
        """
        return self._relative_path


class ListingBuilder(Builder):
    """
    Converts ListingSource instances into Documents.
    """

    def __init__(self, config: PluginSettings) -> None:
        """
        Create a Builder with the given configuration.
        """

    def build(
        self,
        unprocessed: Set[Source],
        processed: Dict[Source, Document],
    ) -> None:
        """
        Consume unprocessed Sources and insert their Documents into processed.
        """
        to_process = set(
            x for x in unprocessed if isinstance(x, ListingSource)
        )
        unprocessed -= to_process

        for source in to_process:
            processed[source] = Document(ListingNode(source.sources))


class ListingNode(Node):
    """
    A node representing a directory listing.
    """

    sources: Final[Set[Source]]

    def __init__(self, sources: Set[Source]) -> None:
        self.sources = sources

    @property
    def children(self) -> Tuple[()]:
        """
        Child nodes belonging to this node.
        """
        return ()

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old node with the given new node.
        """
        raise TypeError()


def render_html(
    context: object,
    parent: object,
    node: object,
) -> html.RenderResult:
    """
    Render a ListingNode as HTML.
    """
    assert isinstance(context, Context)
    assert isinstance(parent, (html.HTMLRoot, html.HTMLTag))
    assert isinstance(node, ListingNode)

    output_path = context[Source].output_path
    entries = []

    for source in node.sources:
        entry_path = source.output_path

        if output_path == entry_path:
            relative_path = ""
        else:
            common_path = commonpath((output_path, entry_path))

            parents = len(output_path.relative_to(common_path).parents) - 1

            relative_path = (
                str(
                    PurePath(*[".."] * parents)
                    / entry_path.relative_to(common_path)
                )
                + ".html"
            )  # TODO: Don't hardcode extension.

        path = source.relative_path or source.output_path
        entries.append((path, relative_path))

    entries.sort()

    env = Environment(
        loader=PackageLoader("docc.plugins.listing"),
        autoescape=select_autoescape(),
    )
    template = env.get_template("listing.html")
    parser = html.HTMLParser(context)
    parser.feed(template.render(context=context, entries=entries))
    for child in parser.root._children:
        parent.append(child)
    return None
