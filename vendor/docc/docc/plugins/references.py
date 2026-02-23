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
Definitions and references for interlinking documents.
"""

import dataclasses
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Set, Tuple, Type

from docc.context import Context, Provider
from docc.document import BlankNode, Document, Node, Visit, Visitor
from docc.settings import PluginSettings
from docc.source import Source
from docc.transform import Transform


@dataclass(eq=True, frozen=True)
class Location:
    """
    Location of a node.
    """

    source: Source
    identifier: str
    specifier: int


class ReferenceError(Exception):
    """
    Exception raised when a reference doesn't match a definition.
    """

    identifier: str
    context: Optional[Context]

    def __init__(
        self, identifier: str, context: Optional[Context] = None
    ) -> None:
        message = f"undefined identifier: `{identifier}`"
        source = None
        if context:
            try:
                source = context[Source]
            except KeyError:
                pass

        if source:
            if source.relative_path:
                message = f"in `{source.relative_path}`, {message}"
            else:
                message = f"writing to `{source.output_path}`, {message}"

        super().__init__(message)
        self.identifier = identifier
        self.context = context


class Index:
    """
    Tracks the location of definitions.
    """

    _index: Dict[str, Set[Location]]

    def __init__(self) -> None:
        self._index = defaultdict(set)

    def define(self, source: Source, identifier: str) -> Location:
        """
        Register a new definition in the index.
        """
        existing = self._index[identifier]
        definition = Location(
            source=source, identifier=identifier, specifier=len(existing)
        )
        existing.add(definition)
        return definition

    def lookup(self, identifier: str) -> Iterable[Location]:
        """
        Find a definition that was previously registered.
        """
        got = self._index[identifier]
        if not got:
            raise ReferenceError(identifier)
        return got


@dataclass(repr=False)
class Base(Node):
    """
    Node implementation for Definition and Reference.
    """

    identifier: str
    child: Node = dataclasses.field(default_factory=BlankNode)

    @property
    def children(self) -> Tuple[Node]:
        """
        Return the children of this node.
        """
        return (self.child,)

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace a child with a different node.
        """
        if old == self.child:
            self.child = new


@dataclass
class Definition(Base):
    """
    A target for a Reference.
    """

    specifier: Optional[int] = dataclasses.field(default=None)


@dataclass
class Reference(Base):
    """
    A link to a Definition.
    """


class IndexContext(Provider[Index]):
    """
    Injects an Index instance into the Context.
    """

    index: Index

    def __init__(self, config: PluginSettings) -> None:
        super().__init__(config)
        self.index = Index()

    @classmethod
    def provides(class_) -> Type[Index]:
        """
        Return the type used as the key in the Context.
        """
        return Index

    def provide(self) -> Index:
        """
        Return the object to add to the Context.
        """
        return self.index


class IndexTransform(Transform):
    """
    Collect Definition nodes and insert them into the index.
    """

    def __init__(self, config: PluginSettings) -> None:
        pass

    def transform(self, context: Context) -> None:
        """
        Apply the transformation to the given document.
        """
        context[Document].root.visit(_TransformVisitor(context))


class _TransformVisitor(Visitor):
    context: Context

    def __init__(self, context: Context) -> None:
        self.context = context

    def enter(self, node: Node) -> Visit:
        if isinstance(node, Definition):
            definition = self.context[Index].define(
                self.context[Source], node.identifier
            )
            assert node.specifier is None
            node.specifier = definition.specifier
        return Visit.TraverseChildren

    def exit(self, node: Node) -> None:
        pass
