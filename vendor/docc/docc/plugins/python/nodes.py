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
Python language support for docc.
"""

import dataclasses
import typing
from dataclasses import dataclass, fields
from typing import Iterable, Literal, Optional, Sequence, Union

from docc.document import BlankNode, ListNode, Node, Visit, Visitor
from docc.plugins.search import Content, Searchable


class PythonNode(Node):
    """
    Base implementation of Node operations for Python nodes.
    """

    @property
    def children(self) -> Iterable[Node]:
        """
        Child nodes belonging to this node.
        """
        for field in fields(self):
            value = getattr(self, field.name)

            if field.type == Node:
                if not isinstance(value, field.type):
                    raise TypeError("child not Node")
                yield value
            else:
                # Not a child, so just ignore it.
                pass

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old node with the given new node.
        """
        for field in fields(self):
            value = getattr(self, field.name)
            if value == old:
                assert isinstance(new, field.type)
                setattr(self, field.name, new)
                continue

    def __repr__(self) -> str:
        """
        Textual representation of this instance.
        """
        return self.__class__.__name__ + "(...)"


@dataclass(repr=False)
class Module(PythonNode, Searchable):
    """
    A Python module.
    """

    name: Node = dataclasses.field(default_factory=BlankNode)
    docstring: Node = dataclasses.field(default_factory=BlankNode)
    members: Node = dataclasses.field(default_factory=ListNode)

    def to_search(self) -> Content:
        """
        Extract the searchable fields from this node.
        """
        return {
            "type": "module",
            "name": _NameVisitor.collect(self.name),
        }


@dataclass(repr=False)
class Class(PythonNode, Searchable):
    """
    A class declaration.
    """

    decorators: Node = dataclasses.field(default_factory=ListNode)
    name: Node = dataclasses.field(default_factory=BlankNode)
    bases: Node = dataclasses.field(default_factory=ListNode)
    metaclass: Node = dataclasses.field(default_factory=BlankNode)
    docstring: Node = dataclasses.field(default_factory=BlankNode)
    members: Node = dataclasses.field(default_factory=ListNode)

    def to_search(self) -> Content:
        """
        Extract the searchable fields from this node.
        """
        return {
            "type": "class",
            "name": _NameVisitor.collect(self.name),
        }


@dataclass(repr=False)
class Function(PythonNode, Searchable):
    """
    A function definition.
    """

    asynchronous: bool
    decorators: Node = dataclasses.field(default_factory=ListNode)
    name: Node = dataclasses.field(default_factory=BlankNode)
    parameters: Node = dataclasses.field(default_factory=ListNode)
    return_type: Node = dataclasses.field(default_factory=BlankNode)
    docstring: Node = dataclasses.field(default_factory=BlankNode)
    body: Node = dataclasses.field(default_factory=BlankNode)

    def to_search(self) -> Content:
        """
        Extract the searchable fields from this node.
        """
        return {
            "type": "function",
            "name": _NameVisitor.collect(self.name),
        }


@dataclass(repr=False)
class Type(PythonNode):
    """
    A type, usually used in a PEP 484 annotation.
    """

    child: Node = dataclasses.field(default_factory=BlankNode)


@dataclass(repr=False)
class Subscript(PythonNode):
    """
    A subscript expression, of the form `name[...]`.
    """

    name: Node = dataclasses.field(default_factory=BlankNode)
    generics: Node = dataclasses.field(default_factory=BlankNode)


@dataclass(repr=False)
class BinaryOperation(PythonNode):
    """
    An operation with two inputs.
    """

    left: Node = dataclasses.field(default_factory=BlankNode)
    operator: Node = dataclasses.field(default_factory=BlankNode)
    right: Node = dataclasses.field(default_factory=BlankNode)


@dataclass(repr=False)
class BitOr(PythonNode):
    """
    A bitwise or operation.
    """


@dataclass(repr=False)
class List(PythonNode):
    """
    Square brackets wrapping a list of elements, usually separated by commas.
    """

    elements: Node = dataclasses.field(default_factory=ListNode)


@dataclass(repr=False)
class Tuple(PythonNode):
    """
    Parentheses wrapping a list of elements, usually separated by commas.
    """

    elements: Node = dataclasses.field(default_factory=ListNode)


@dataclass(repr=False)
class Parameter(PythonNode):
    """
    A parameter descriptor in a function definition.
    """

    star: Optional[Union[Literal["*"], Literal["**"]]] = None
    name: Node = dataclasses.field(default_factory=BlankNode)
    type_annotation: Node = dataclasses.field(default_factory=BlankNode)
    default_value: Node = dataclasses.field(default_factory=BlankNode)


@dataclass(repr=False)
class Attribute(PythonNode, Searchable):
    """
    An assignment.
    """

    names: Node = dataclasses.field(default_factory=ListNode)
    body: Node = dataclasses.field(default_factory=BlankNode)
    docstring: Node = dataclasses.field(default_factory=BlankNode)

    def to_search(self) -> Content:
        """
        Extract the searchable fields from this node.
        """
        return {
            "type": "attribute",
            "name": _NameVisitor.collect(self.names),
        }


@dataclass
class Name(Node):
    """
    The name of a class, function, variable, or other Python member.
    """

    name: str
    full_name: Optional[str] = dataclasses.field(default=None)

    @property
    def children(self) -> Iterable[Node]:
        """
        Child nodes belonging to this node.
        """
        return tuple()

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old node with the given new node.
        """
        raise TypeError()


@dataclass(repr=False)
class Access(PythonNode):
    """
    One level of attribute access.

    The example `foo.bar.baz` should be represented as:

    ```python
    Access(
        value=Access(
            value=Name(name="foo"),
            attribute=Name(name="bar"),
        ),
        attribute=Name(name="baz"),
    )
    ```
    """

    value: Node = dataclasses.field(default_factory=BlankNode)
    attribute: Node = dataclasses.field(default_factory=BlankNode)


@dataclass
class Docstring(Node, Searchable):
    """
    Node representing a documentation string.
    """

    text: str

    @property
    def children(self) -> Iterable[Node]:
        """
        Child nodes belonging to this node.
        """
        return tuple()

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old node with the given new node.
        """
        raise TypeError()

    def to_search(self) -> Content:
        """
        Extract the searchable fields from this node.
        """
        return self.text


class _NameVisitor(Visitor):
    names: typing.List[str]

    @staticmethod
    def collect(nodes: Union[Node, Sequence[Node]]) -> typing.List[str]:
        if isinstance(nodes, Node):
            nodes = [nodes]

        visitor = _NameVisitor()

        for node in nodes:
            node.visit(visitor)

        return visitor.names

    def __init__(self) -> None:
        self.names = []

    def enter(self, node: Node) -> Visit:
        if isinstance(node, Name):
            self.names.append(node.name)
            return Visit.SkipChildren
        return Visit.TraverseChildren

    def exit(self, node: Node) -> None:
        pass
