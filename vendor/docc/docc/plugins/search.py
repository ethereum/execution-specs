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
Utilities for search.
"""

import json
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from io import TextIOBase
from pathlib import PurePath
from typing import (
    DefaultDict,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Type,
    Union,
)

from typing_extensions import TypeAlias, assert_never

from docc.build import Builder
from docc.context import Context, Provider
from docc.discover import Discover
from docc.document import BlankNode, Document, Node, OutputNode, Visit, Visitor
from docc.plugins.references import Definition, Index, ReferenceError
from docc.settings import PluginSettings
from docc.source import Source
from docc.transform import Transform


@dataclass(eq=True, frozen=True)
class BySource:
    """
    Location of a search item using a source.
    """

    source: Source


@dataclass(eq=True, frozen=True)
class ByReference:
    """
    Location of a search item using a reference.
    """

    identifier: str
    specifier: Optional[int]


Location: TypeAlias = BySource | ByReference
Content: TypeAlias = Union[str, Mapping[str, Union[str, Sequence[str]]]]


@dataclass(eq=True, frozen=True)
class Item:
    """
    A searchable item.
    """

    location: Location
    content: Content


class Search:
    """
    Tracks searchable items.
    """

    _items: DefaultDict[Location, DefaultDict[str, List[str]]]

    def __init__(self) -> None:
        self._items = defaultdict(lambda: defaultdict(list))

    def add(self, item: Item) -> None:
        """
        Add the given `item` to the search index.
        """
        existing = self._items[item.location]
        raw_content = item.content

        if isinstance(raw_content, str):
            raw_content = {"text": [raw_content]}

        for key, value in raw_content.items():
            if isinstance(value, str):
                existing[key].append(value)
            else:
                existing[key].extend(value)


class SearchSource(Source):
    """
    A virtual source for a search index.
    """

    @property
    def relative_path(self) -> None:
        """
        Path to the Source (if one exists) relative to the project root.
        """
        return None

    @property
    def output_path(self) -> PurePath:
        """
        Where to write the output from this Source relative to the output path.
        """
        return PurePath("search")


class SearchBuilder(Builder):
    """
    Consumes unprocessed Sources and creates Documents.
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
        to_process = set(x for x in unprocessed if isinstance(x, SearchSource))
        unprocessed -= to_process

        for source in to_process:
            processed[source] = Document(SearchNode())


class SearchNode(BlankNode, OutputNode):
    """
    Placeholder for a search index.
    """

    @property
    def extension(self) -> str:
        """
        The preferred file extension for this node.
        """
        return ".js"

    def output(self, context: Context, destination: TextIOBase) -> None:
        """
        Write this Node to destination.
        """
        items = context[Search]._items

        output = []
        for location, content in items.items():
            output_source = {}

            # Find the source associated with the item.
            if isinstance(location, BySource):
                source = location.source
            elif isinstance(location, ByReference):
                definitions = context[Index].lookup(location.identifier)
                output_source["identifier"] = location.identifier

                if location.specifier is None:
                    source = list(definitions)[0].source
                else:
                    output_source["specifier"] = location.specifier
                    source_opt = None
                    for definition in definitions:
                        if definition.specifier == location.specifier:
                            source_opt = definition.source
                            break

                    if source_opt:
                        source = source_opt
                    else:
                        raise ReferenceError(location.identifier)
            else:
                assert_never(location.__class__)

            output_source["path"] = str(source.output_path)

            output.append(
                {
                    "source": output_source,
                    "content": content,
                }
            )

        destination.write("this.SEARCH_INDEX = ")
        json.dump(output, destination)  # type: ignore
        destination.write("; Object.freeze(this.SEARCH_INDEX);")


class SearchDiscover(Discover):
    """
    Finds sources for which to generate documentation.
    """

    def __init__(self, settings: PluginSettings) -> None:
        pass

    def discover(self, known: object) -> Iterator[Source]:
        """
        Find sources.
        """
        yield SearchSource()


class SearchContext(Provider[Search]):
    """
    Provides a Search item for the Context.
    """

    search: Search

    def __init__(self, settings: PluginSettings) -> None:
        super().__init__(settings)
        self.search = Search()

    @classmethod
    def provides(class_) -> Type[Search]:
        """
        Return the type to be used as the key in the Context.
        """
        return Search

    def provide(self) -> Search:
        """
        Create the object to be inserted into the Context.
        """
        return self.search


class SearchTransform(Transform):
    """
    Walks the document tree to discover searchable nodes.
    """

    def __init__(self, settings: PluginSettings) -> None:
        pass

    def transform(self, context: Context) -> None:
        """
        Apply the transformation to the given document.
        """
        document = context[Document]
        document.root.visit(_SearchVisitor(context))


class Searchable(ABC):
    """
    Base class for objects that can be searched.
    """

    @abstractmethod
    def to_search(self) -> Content:
        """
        Extract searchable fields from the node.
        """

    def search_children(self) -> bool:
        """
        `True` if the children of this node should be searched, or `False`
        otherwise.
        """
        return True


class _SearchVisitor(Visitor):
    context: Context
    _definitions: List[Definition]

    def __init__(self, context: Context) -> None:
        self.context = context
        self._definitions = []

    def _enter_searchable(self, node: Searchable) -> Visit:
        if self._definitions:
            definition = self._definitions[-1]
            location = ByReference(
                identifier=definition.identifier,
                specifier=definition.specifier,
            )
        else:
            location = BySource(source=self.context[Source])

        self.context[Search].add(
            Item(
                location=location,
                content=node.to_search(),
            )
        )

        if node.search_children():
            return Visit.TraverseChildren
        else:
            return Visit.SkipChildren

    def enter(self, node: Node) -> Visit:
        if isinstance(node, Definition):
            self._definitions.append(node)

        if isinstance(node, Searchable):
            return self._enter_searchable(node)

        return Visit.TraverseChildren

    def exit(self, node: Node) -> None:
        if isinstance(node, Definition):
            popped = self._definitions.pop()
            assert node == popped
