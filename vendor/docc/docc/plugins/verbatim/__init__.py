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
Support for copying verbatim text from a Source into the output, with syntax
highlighting support.
"""

import logging
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Final, Iterable, List, Optional, Sequence, Tuple, Union

from docc.context import Context
from docc.document import Document, Node, Visit, Visitor
from docc.plugins import references
from docc.settings import PluginSettings
from docc.source import TextSource
from docc.transform import Transform


@dataclass
class Transcribed(Node):
    """
    A block of verbatim text.

    Unlike `Verbatim` nodes, `Transcribed` blocks actually contain the text
    from the `Source`, instead of a line numbers and ranges. This makes them
    more useful for further processing.
    """

    _children: List[Node] = field(default_factory=list)

    @property
    def children(self) -> Iterable[Node]:
        """
        Child nodes belonging to this node.
        """
        return self._children

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old node with the new node.
        """
        self._children = [new if x == old else x for x in self._children]

    def __repr__(self) -> str:
        """
        String representation of this node.
        """
        return "Transcribed(...)"


@dataclass
class Line(Node):
    """
    A grouping of nodes occupying the same line.
    """

    number: int
    _children: List[Node] = field(default_factory=list)

    @property
    def children(self) -> Iterable[Node]:
        """
        Child nodes belonging to this node.
        """
        return self._children

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old child with the new one.
        """
        self._children = [new if x == old else x for x in self._children]

    def __repr__(self) -> str:
        """
        String representation of this node.
        """
        return f"Line(number={self.number}, ...)"


@dataclass
class Highlight(Node):
    """
    Node with highlighting information.
    """

    highlights: List[str] = field(default_factory=list)
    _children: List[Node] = field(default_factory=list)

    @property
    def children(self) -> Sequence[Node]:
        """
        Return the children of this node.
        """
        return self._children

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old child with the provided new one.
        """
        self._children = [new if x == old else x for x in self._children]

    def __repr__(self) -> str:
        """
        String representation of this node.
        """
        return f"Highlight(highlights={self.highlights!r}, ...)"


@dataclass
class Text(Node):
    """
    Node containing simple text.
    """

    text: str

    @property
    def children(self) -> Tuple[()]:
        """
        Return the children of this node.
        """
        return ()

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old child with a new one.
        """
        raise TypeError()


class VerbatimNode(Node):
    """
    Base class for verbatim nodes.
    """

    _children: List[Node]

    def __init__(self) -> None:
        self._children = []

    @property
    def children(self) -> Iterable[Node]:
        """
        Child nodes belonging to this node.
        """
        return self._children

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old node with the given new node.
        """
        self._check(new)
        for index, child in enumerate(self._children):
            if child == old:
                self._children[index] = new

    def append(self, new: Node) -> None:
        """
        Append a new child node.
        """
        self._check(new)
        self._children.append(new)

    def _check(self, new: Node) -> None:
        if isinstance(new, Verbatim):
            # TODO: is it worth checking children of children?
            class_ = new.__class__.__name__
            raise ValueError(f"cannot nest a {class_} in a verbatim node")


@dataclass(order=True)
class _Pos:
    line: int
    column: int


@dataclass(order=True, frozen=True, repr=False)
class Pos:
    """
    Position in a Source.
    """

    line: int
    column: int

    def __repr__(self) -> str:
        """
        Textual representation of this instance.
        """
        return f"{self.line}:{self.column}"


class Verbatim(VerbatimNode):
    """
    A block of lines of text from one Source.
    """

    source: TextSource

    def __init__(self, source: TextSource) -> None:
        super().__init__()
        self.source = source

    def __repr__(self) -> str:
        """
        Textual representation of this instance.
        """
        return f"Verbatim({self.source!r})"


class Fragment(VerbatimNode):
    """
    A snippet of text from a Source.
    """

    start: Pos
    end: Pos

    highlights: List[str]

    def __init__(
        self, start: Pos, end: Pos, highlights: Optional[List[str]] = None
    ) -> None:
        super().__init__()
        self.start = start
        self.end = end
        self.highlights = [] if highlights is None else highlights

    def __repr__(self) -> str:
        """
        Textual representation of this instance.
        """
        return f"Fragment({self.start}, {self.end}, {self.highlights!r})"


@dataclass
class _VerbatimContext:
    node: Verbatim
    written: Optional[_Pos] = None

    @property
    def source(self) -> TextSource:
        return self.node.source


class _BoundsVisitor(Visitor):
    start: Optional[Pos]
    end: Optional[Pos]

    def __init__(self) -> None:
        self.start = None
        self.end = None

    def enter(self, node: Node) -> Visit:
        if isinstance(node, Fragment):
            if self.start is None or node.start < self.start:
                self.start = node.start

            if self.end is None or node.end > self.end:
                self.end = node.end

        return Visit.TraverseChildren

    def exit(self, node: Node) -> None:
        pass


class VerbatimVisitor(Visitor):
    """
    Visitor for verbatim node trees that emits a series of events.
    """

    # TODO: I wonder if there's a way to visit all nodes, put them in a heap,
    #       and read the text that way.

    _depth: Optional[int]
    _verbatim: Optional[_VerbatimContext]

    def __init__(self) -> None:
        super().__init__()
        self._depth = None
        self._verbatim = None

    #
    # Override in Subclasses:
    #

    @abstractmethod
    def line(self, source: TextSource, line: int) -> None:
        """
        Marks the start of a new line.
        """

    @abstractmethod
    def text(self, text: str) -> None:
        """
        String copied from the Source.
        """

    @abstractmethod
    def begin_highlight(self, highlights: Sequence[str]) -> None:
        """
        Marks the start of a highlighted section.
        """

    @abstractmethod
    def end_highlight(self) -> None:
        """
        Marks the end of a highlighted section.
        """

    def enter_node(self, node: Node) -> Visit:
        """
        Visit a non-verbatim Node.
        """
        if node:
            logging.warning(
                "`%s` entered non-verbatim node `%s`",
                self.__class__.__name__,
                node.__class__.__name__,
            )
        return Visit.TraverseChildren

    def exit_node(self, node: Node) -> None:
        """
        Leave a non-verbatim Node.
        """
        if node:
            logging.warning(
                "`%s` exited non-verbatim node `%s`",
                self.__class__.__name__,
                node.__class__.__name__,
            )

    #
    # Implementation Details:
    #

    def _copy(self, start_line: int, until: Pos) -> None:
        verbatim = self._verbatim

        assert verbatim is not None
        assert until.line > 0
        assert until.column >= 0

        if verbatim.written is None:
            verbatim.written = _Pos(
                line=start_line,
                column=0,
            )
            self.line(verbatim.source, verbatim.written.line)

        written = verbatim.written
        assert written is not None

        while written.line < until.line:
            text = verbatim.source.line(written.line)
            self.text(text[written.column :])

            written.line += 1
            written.column = 0

            self.line(verbatim.source, written.line)

        if written.line > until.line:
            return

        if written.column >= until.column:
            return

        text = verbatim.source.line(written.line)
        self.text(text[written.column : until.column])

        written.column = until.column

    def _enter_fragment(self, node: Fragment) -> Visit:
        depth = self._depth

        if depth is None or depth < 1:
            raise Exception("Fragment nodes must appear inside Verbatim")

        self._copy(node.start.line, node.start)

        self._depth = depth + 1
        self.begin_highlight(node.highlights)

        return Visit.TraverseChildren

    def _exit_fragment(self, node: Fragment) -> None:
        depth = self._depth
        assert depth is not None
        assert depth > 1

        self._copy(node.start.line, node.end)
        self.end_highlight()

        self._depth = depth - 1

    def _enter_verbatim(self, node: Verbatim) -> Visit:
        if self._depth is not None:
            raise Exception("Verbatim nodes cannot be nested")
        self._depth = 1
        self._verbatim = _VerbatimContext(node)
        return Visit.TraverseChildren

    def _exit_verbatim(self, node: Verbatim) -> None:
        assert self._depth == 1
        assert self._verbatim is not None
        assert self._verbatim.node == node
        self._verbatim = None
        self._depth = None

    def enter(self, node: Node) -> Visit:
        """
        Visit a node.
        """
        if isinstance(node, Fragment):
            return self._enter_fragment(node)
        elif isinstance(node, Verbatim):
            return self._enter_verbatim(node)
        else:
            # TODO: Save the results somewhere so we don't visit twice.
            visitor = _BoundsVisitor()
            node.visit(visitor)
            if visitor.start is not None:
                self._copy(visitor.start.line, visitor.start)
            return self.enter_node(node)

    def exit(self, node: Node) -> None:
        """
        Depart a node.
        """
        if isinstance(node, Fragment):
            return self._exit_fragment(node)
        elif isinstance(node, Verbatim):
            return self._exit_verbatim(node)
        else:
            # TODO: Save the results somewhere so we don't visit twice.
            visitor = _BoundsVisitor()
            node.visit(visitor)
            if visitor.end is not None:
                start = visitor.start or visitor.end
                self._copy(start.line, visitor.end)
            return self.exit_node(node)


class _TranscribeVisitor(VerbatimVisitor):
    context: Final[Context]
    document: Final[Document]
    root: Transcribed
    output_stack: List[Node]
    input_stack: List[Sequence[str] | references.Reference]

    def __init__(self, context: Context) -> None:
        super().__init__()
        self.context = context
        self.document = context[Document]

        self.root = Transcribed()

        self.output_stack = []
        self.input_stack = []

    def line(self, source: TextSource, line: int) -> None:
        line_node = Line(number=line)
        self.root._children.append(line_node)
        self.output_stack = [line_node]
        self._highlight(self.input_stack)

    def _highlight(
        self,
        highlight_groups: Sequence[Union[Sequence[str], references.Reference]],
    ) -> None:
        for item in highlight_groups:
            top = self.output_stack[-1]

            if isinstance(item, references.Reference):
                new_node = references.Reference(identifier=item.identifier)
            else:
                new_node = Highlight(highlights=list(item))

            if isinstance(top, references.Reference):
                assert not top.child
                top.child = new_node
            elif isinstance(top, (Highlight, Line)):
                top._children.append(new_node)
            else:
                raise TypeError(
                    f"expected Highlight or Line, got `{type(top)}`"
                )

            self.output_stack.append(new_node)

    def text(self, text: str) -> None:
        top = self.output_stack[-1]
        new_node = Text(text)
        if isinstance(top, references.Reference):
            assert not top.child
            top.child = new_node
        elif isinstance(top, (Highlight, Line)):
            top._children.append(new_node)
        else:
            raise TypeError(f"expected Highlight or Line, got `{type(top)}`")

    def begin_highlight(self, highlights: Sequence[str]) -> None:
        self.input_stack.append(highlights)
        self._highlight([highlights])

    def end_highlight(self) -> None:
        self.input_stack.pop()
        popped_node = self.output_stack.pop()
        assert isinstance(popped_node, Highlight)

    def enter_node(self, node: Node) -> Visit:
        """
        Visit a non-verbatim Node.
        """
        if isinstance(node, references.Reference):
            if "<" in node.identifier:
                # TODO: Create definitions for local variables.
                return Visit.TraverseChildren
            self.input_stack.append(node)
            if self.output_stack:
                self._highlight([node])
            return Visit.TraverseChildren
        else:
            return super().enter_node(node)

    def exit_node(self, node: Node) -> None:
        """
        Leave a non-verbatim Node.
        """
        if isinstance(node, references.Reference):
            if "<" in node.identifier:
                # TODO: Create definitions for local variables.
                return

            popped = self.input_stack.pop()
            assert popped == node

            popped_output = self.output_stack.pop()
            assert isinstance(
                popped_output, (Line, Highlight, references.Reference)
            )
        else:
            return super().exit_node(node)


class _FindVisitor(Visitor):
    context: Context
    stack: List[Node]
    root: Optional[Node]

    def __init__(self, context: Context) -> None:
        self.context = context
        self.stack = []
        self.root = None

    def enter(self, node: Node) -> Visit:
        self.stack.append(node)
        if self.root is None:
            self.root = node

        if not isinstance(node, Verbatim):
            return Visit.TraverseChildren

        visitor = _TranscribeVisitor(self.context)
        node.visit(visitor)

        if len(self.stack) == 1:
            self.root = visitor.root
        else:
            self.stack[-2].replace_child(node, visitor.root)

        return Visit.SkipChildren

    def exit(self, node: Node) -> None:
        self.stack.pop()


class Transcribe(Transform):
    """
    A plugin that converts position-based Verbatim nodes into transcribed
    nodes.
    """

    def __init__(self, settings: PluginSettings) -> None:
        pass

    def transform(self, context: Context) -> None:
        """
        Apply the transformation to the given document.
        """
        document = context[Document]

        visitor = _FindVisitor(context)
        document.root.visit(visitor)
        assert visitor.root is not None
        document.root = visitor.root
