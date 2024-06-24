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
Plugins for docc specific to the Ethereum execution specification.
"""

import dataclasses
import logging
from collections import defaultdict
from itertools import tee, zip_longest
from pathlib import PurePath
from typing import (
    Dict,
    Final,
    FrozenSet,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from docc.context import Context
from docc.discover import Discover, T
from docc.document import BlankNode, Document, ListNode, Node, Visit, Visitor
from docc.plugins import html, mistletoe, python, verbatim
from docc.plugins.listing import Listable
from docc.plugins.python import PythonBuilder
from docc.plugins.references import Definition, Reference
from docc.settings import PluginSettings
from docc.source import Source
from docc.transform import Transform
from fladrif.apply import Apply
from fladrif.treediff import Adapter, Operation, TreeMatcher
from mistletoe import block_token as blocks  # type: ignore
from mistletoe import span_token as spans
from typing_extensions import assert_never, override

from .forks import Hardfork

G = TypeVar("G")


def pairwise(iterable: Iterable[G]) -> Iterable[Tuple[G, G]]:
    """
    ABCDEFG --> AB BC CD DE EF FG
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


class EthereumDiscover(Discover):
    """
    Creates sources that represent the diff between two other sources, one per
    fork.
    """

    forks: List[Hardfork]
    settings: PluginSettings

    def __init__(self, config: PluginSettings) -> None:
        self.settings = config
        base = config.resolve_path(PurePath("src") / "ethereum")
        self.forks = Hardfork.discover(base=base)

    def discover(self, known: FrozenSet[T]) -> Iterator[Source]:
        """
        Find sources.
        """
        forks = {f.path: f for f in self.forks if f.path is not None}

        by_fork: Dict[Hardfork, Dict[PurePath, Source]] = defaultdict(dict)

        for source in known:
            if not source.relative_path:
                continue

            absolute_path = self.settings.resolve_path(source.relative_path)

            for fork_path, fork_fork in forks.items():
                try:
                    fork_relative_path = absolute_path.relative_to(fork_path)
                    fork = fork_fork
                    break
                except ValueError:
                    logging.debug(
                        "source `%s` is not part of fork `%s`",
                        source.relative_path,
                        fork_fork.short_name,
                        exc_info=True,
                    )
            else:
                continue

            if fork_relative_path in by_fork[fork]:
                raise Exception(
                    f"two sources claim same path `{fork_relative_path}`"
                )

            by_fork[fork][fork_relative_path] = source

        diff_count = 0
        for before, after in pairwise(self.forks):
            paths = set(by_fork[before].keys()) | set(by_fork[after].keys())

            for path in paths:
                diff_count += 1
                before_source = by_fork[before].get(path, None)
                after_source = by_fork[after].get(path, None)

                assert before_source or after_source

                output_path = (
                    PurePath("diffs")
                    / before.short_name
                    / after.short_name
                    / path
                )

                yield DiffSource(
                    before.name,
                    before_source,
                    after.name,
                    after_source,
                    output_path,
                )

        if 0 == diff_count:
            raise Exception("no diff pairs found")

        logging.info("Discovered %s pair(s) of sources to diff", diff_count)


S = TypeVar("S", bound=Source)


class DiffSource(Generic[S], Source, Listable):
    """
    A source that represents the difference between two other sources.
    """

    before_name: str
    before: Optional[S]

    after_name: str
    after: Optional[S]
    _output_path: PurePath

    def __init__(
        self,
        before_name: str,
        before: Optional[S],
        after_name: str,
        after: Optional[S],
        output_path: PurePath,
    ) -> None:
        self.before_name = before_name
        self.before = before

        self.after_name = after_name
        self.after = after

        self._output_path = output_path

    @property
    def show_in_listing(self) -> bool:
        """
        True if this source should appear in directory listings.
        """
        return True

    @property
    def relative_path(self) -> Optional[PurePath]:
        """
        Path to the Source (if one exists) relative to the project root.
        """
        return None

    @property
    def output_path(self) -> PurePath:
        """
        Where to write the output from this Source relative to the output path.
        """
        return self._output_path


class AfterNode(Node):
    """
    Represents content that was added in a diff.
    """

    child: Node

    def __init__(self, child: Node) -> None:
        self.child = child

    @property
    def children(self) -> Tuple[Node]:
        """
        Child nodes belonging to this node.
        """
        return (self.child,)

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old node with the given new node.
        """
        if self.child == old:
            self.child = new

    def __repr__(self) -> str:
        """
        String representation of this node.
        """
        return "<after>"


class BeforeNode(Node):
    """
    Represents content that was removed in a diff.
    """

    child: Node

    def __init__(self, child: Node) -> None:
        self.child = child

    @property
    def children(self) -> Tuple[Node]:
        """
        Child nodes belonging to this node.
        """
        return (self.child,)

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old node with the given new node.
        """
        if self.child == old:
            self.child = new

    def __repr__(self) -> str:
        """
        String representation of this node.
        """
        return "<before>"


class DiffNode(Node):
    """
    Marks a difference (or patch) with a deletion and an insertion.
    """

    before_name: str
    before: Node

    after_name: str
    after: Node

    def __init__(
        self, before_name: str, before: Node, after_name: str, after: Node
    ) -> None:
        self.before_name = before_name
        self.before = before

        self.after_name = after_name
        self.after = after

    @property
    def children(self) -> Tuple[Node, Node]:
        """
        Child nodes belonging to this node.
        """
        return (self.before, self.after)

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old node with the given new node.
        """
        if self.before == old:
            self.before = new
        if self.after == old:
            self.after = new

    def __repr__(self) -> str:
        """
        String representation of this object.
        """
        return (
            f"{self.__class__.__name__}(..., "
            f"before_name={self.before_name!r}, "
            f"after_name={self.after_name!r})"
        )


class EthereumBuilder(PythonBuilder):
    """
    A `PythonBuilder` that additionally builds `Document`s from `DiffSource`s.
    """

    def build(
        self,
        unprocessed: Set[Source],
        processed: Dict[Source, Document],
    ) -> None:
        """
        Consume unprocessed Sources and insert their Documents into processed.
        """
        # Build normal Python documents.
        super().build(unprocessed, processed)

        # Build diff documents.
        source_set = set(s for s in unprocessed if isinstance(s, DiffSource))
        unprocessed -= source_set

        before_unprocessed = {s.before for s in source_set if s.before}
        after_unprocessed = {s.after for s in source_set if s.after}

        # Rebuild the sources so we get distinct tree objects.
        before_processed: Dict[Source, Document] = dict()
        after_processed: Dict[Source, Document] = dict()

        super().build(before_unprocessed, before_processed)
        super().build(after_unprocessed, after_processed)

        for diff_source in source_set:
            before: Node = BlankNode()
            if diff_source.before:
                before_document = before_processed[diff_source.before]
                del before_processed[diff_source.before]
                before = BeforeNode(before_document.root)

            after: Node = BlankNode()
            if diff_source.after:
                after_document = after_processed[diff_source.after]
                del after_processed[diff_source.after]
                after = AfterNode(after_document.root)

            root = DiffNode(
                diff_source.before_name, before, diff_source.after_name, after
            )
            document = Document(root)
            processed[diff_source] = document


class FixIndexTransform(Transform):
    """
    Replaces `Definition` and `Reference` identifiers within `DiffNode` with
    identifiers specific to the diff.

    Without fixing these identifiers, every Python class would be defined
    multiples times (the actual definition and then again in each diff),
    cluttering up tables of contents.
    """

    def __init__(self, settings: PluginSettings) -> None:
        pass

    def transform(self, context: Context) -> None:
        """
        Apply the transformation to the given document.
        """
        context[Document].root.visit(_FixIndexVisitor())


class _FixIndexVisitor(Visitor):
    diffs: Final[List[DiffNode]]

    def __init__(self) -> None:
        self.diffs = []

    def enter(self, node: Node) -> Visit:
        if isinstance(node, DiffNode):
            self.diffs.append(node)
            return Visit.TraverseChildren

        if not self.diffs:
            return Visit.TraverseChildren

        diff = self.diffs[-1]
        before = diff.before_name
        after = diff.after_name

        before_prefix = f"{before}."
        after_prefix = f"{after}."

        if isinstance(node, (Reference, Definition)):
            identifier: Optional[str] = None

            if node.identifier.startswith(before_prefix):
                identifier = node.identifier.removeprefix(before_prefix)
            elif node.identifier.startswith(after_prefix):
                identifier = node.identifier.removeprefix(after_prefix)

            if identifier is not None:
                node.identifier = f"diff({before},{after}).{identifier}"
        elif isinstance(node, python.Name) and node.full_name:
            if node.full_name:
                full_name: Optional[str] = None

                if node.full_name.startswith(before_prefix):
                    full_name = node.full_name.removeprefix(before_prefix)
                elif node.full_name.startswith(after_prefix):
                    full_name = node.full_name.removeprefix(after_prefix)

                if full_name is not None:
                    node.full_name = f"diff({before},{after}).{full_name}"

        return Visit.TraverseChildren

    def exit(self, node: Node) -> None:
        if isinstance(node, DiffNode):
            popped = self.diffs.pop()
            assert popped == node


class _DoccAdapter(Adapter[Node]):
    def children(self, node: Node) -> Sequence[Node]:
        return list(node.children)

    def _markdown_equals(
        self,
        lhs_node: mistletoe.MarkdownNode,
        rhs_node: mistletoe.MarkdownNode,
    ) -> bool:
        lhs = lhs_node.token
        rhs = rhs_node.token

        if not isinstance(rhs, type(lhs)) or not isinstance(lhs, type(rhs)):
            return False

        match type(lhs):
            case (
                spans.Strong
                | spans.Emphasis
                | spans.InlineCode
                | spans.Strikethrough
                | spans.EscapeSequence
                | blocks.Quote
                | blocks.Paragraph
                | blocks.ThematicBreak
                | blocks.HTMLBlock
                | spans.AutoLink
            ):
                return True
            case spans.RawText | spans.HTMLSpan:
                return lhs.content == rhs.content
            case spans.Image:
                return (
                    lhs.src == rhs.src
                    and lhs.title == rhs.title
                    and lhs.label == rhs.label
                )
            case spans.Link:
                return (
                    lhs.target == rhs.target
                    and lhs.title == rhs.title
                    and lhs.label == rhs.label
                )
            case blocks.Heading | blocks.SetextHeading:
                return lhs.level == rhs.level
            case blocks.CodeFence:
                return (
                    lhs.language == rhs.language
                    and lhs.info_string == rhs.info_string
                )
            case blocks.BlockCode:
                return lhs.language == rhs.language
            case blocks.List:
                return lhs.loose == rhs.loose and lhs.start == rhs.start
            case blocks.ListItem:
                return (
                    lhs.loose == rhs.loose
                    and lhs.leader == rhs.leader
                    and lhs.prepend == rhs.prepend
                )
            case blocks.Table:
                return lhs.column_align == rhs.column_align
            case blocks.TableRow:
                return lhs.row_align == rhs.row_align
            case blocks.TableCell:
                return lhs.align == rhs.align
            case spans.LineBreak:
                return lhs.soft == rhs.soft
            case blocks.Document:
                if lhs.footnotes or rhs.footnotes:
                    logging.warning("markdown footnotes not implemented")
                return True
            case _:
                raise NotImplementedError(
                    f"markdown comparison for {lhs} not implemented"
                )

    def _markdown_hash(self, node: mistletoe.MarkdownNode) -> int:
        token = node.token

        result: Tuple[object, ...]
        match type(token):
            case (
                spans.Strong
                | spans.Emphasis
                | spans.InlineCode
                | spans.Strikethrough
                | spans.EscapeSequence
                | blocks.Quote
                | blocks.Paragraph
                | blocks.ThematicBreak
                | blocks.HTMLBlock
                | spans.AutoLink
            ):
                result = ()
            case spans.RawText | spans.HTMLSpan:
                result = (token.content,)
            case spans.Link:
                result = (token.target, token.title, token.label)
            case spans.Image:
                result = (token.src, token.title, token.label)
            case blocks.Heading | blocks.SetextHeading:
                result = (token.level,)
            case blocks.CodeFence:
                result = (token.language, token.info_string)
            case blocks.BlockCode:
                result = (token.language,)
            case blocks.List:
                result = (token.loose, token.start)
            case blocks.ListItem:
                result = (token.loose, token.leader, token.prepend)
            case blocks.Table:
                result = (token.column_align,)
            case blocks.TableRow:
                result = (token.row_align,)
            case blocks.TableCell:
                result = (token.align,)
            case spans.LineBreak:
                result = (token.soft,)
            case blocks.Document:
                if token.footnotes:
                    logging.warning("markdown footnotes not implemented")
                result = ()
            case _:
                raise NotImplementedError(
                    f"markdown hash for {token} not implemented"
                )

        return hash((type(token), result))

    def shallow_equals(self, lhs: Node, rhs: Node) -> bool:
        if lhs is rhs:
            return True

        if not isinstance(lhs, type(rhs)):
            return False

        if not isinstance(rhs, type(lhs)):
            return False

        if isinstance(lhs, python.PythonNode):
            assert isinstance(rhs, python.PythonNode)
            return self._python_equals(lhs, rhs)

        elif isinstance(lhs, Definition):
            assert isinstance(rhs, Definition)
            return (
                lhs.identifier == rhs.identifier
                and lhs.specifier == rhs.specifier
            )

        elif isinstance(lhs, Reference):
            assert isinstance(rhs, Reference)
            return lhs.identifier == rhs.identifier

        elif isinstance(lhs, BlankNode):
            assert isinstance(rhs, BlankNode)
            return True

        elif isinstance(lhs, mistletoe.MarkdownNode):
            assert isinstance(rhs, mistletoe.MarkdownNode)
            return self._markdown_equals(lhs, rhs)

        elif isinstance(lhs, python.Name):
            assert isinstance(rhs, python.Name)
            return lhs.name == rhs.name and lhs.full_name == rhs.full_name

        elif isinstance(lhs, ListNode):
            assert isinstance(rhs, ListNode)
            return True

        elif isinstance(lhs, verbatim.Transcribed):
            assert isinstance(rhs, verbatim.Transcribed)
            return True

        elif isinstance(lhs, verbatim.Line):
            assert isinstance(rhs, verbatim.Line)

            # We want to treat lines as indivisible for the purposes of diffs.
            lefts = list(lhs.children)
            rights = list(rhs.children)
            if len(lefts) != len(rights):
                return False
            return all(self.deep_equals(a, b) for a, b in zip(lefts, rights))

        elif isinstance(lhs, verbatim.Highlight):
            assert isinstance(rhs, verbatim.Highlight)
            return lhs.highlights == rhs.highlights

        elif isinstance(lhs, verbatim.Text):
            assert isinstance(rhs, verbatim.Text)
            return lhs.text == rhs.text

        raise NotImplementedError(f"shallow_equals({type(lhs)}, {type(rhs)})")

    def _python_hash(self, node: python.PythonNode) -> int:
        assert dataclasses.is_dataclass(node)
        hash_value = 0
        for idx, field in enumerate(dataclasses.fields(node)):
            value = getattr(node, field.name)

            if field.type == Node:
                continue
            elif field.type == Sequence[Node]:
                raise ValueError("python node fields can't be sequences")

            hash_value ^= hash((idx, value))
        return hash_value

    def _python_equals(
        self, lhs: python.PythonNode, rhs: python.PythonNode
    ) -> bool:
        assert dataclasses.is_dataclass(lhs)
        assert dataclasses.is_dataclass(rhs)
        assert type(lhs) is type(rhs)

        for field in dataclasses.fields(lhs):
            lhs_value = getattr(lhs, field.name)
            rhs_value = getattr(rhs, field.name)

            if field.type == Node:
                continue
            elif field.type == Sequence[Node]:
                raise ValueError("python node fields can't be sequences")

            if lhs_value != rhs_value:
                return False
        return True

    def shallow_hash(self, node: Node) -> int:
        if isinstance(node, python.PythonNode):
            return self._python_hash(node)

        elif isinstance(node, Definition):
            return hash((node.identifier, None, node.specifier))

        elif isinstance(node, Reference):
            return hash((node.identifier, None))

        elif isinstance(node, BlankNode):
            return hash(type(BlankNode))

        elif isinstance(node, mistletoe.MarkdownNode):
            return self._markdown_hash(node)

        elif isinstance(node, python.Name):
            return hash((node.name, node.full_name))

        elif isinstance(node, ListNode):
            return hash(type(ListNode))

        elif isinstance(node, verbatim.Transcribed):
            return hash(type(verbatim.Transcribed))

        elif isinstance(node, verbatim.Line):
            return hash(type(verbatim.Line))

        elif isinstance(node, verbatim.Highlight):
            return hash(tuple(node.highlights))

        elif isinstance(node, verbatim.Text):
            return hash(node.text)

        raise NotImplementedError(f"shallow_hash({type(node)})")


class _HardenVisitor(Visitor):
    _stack: Final[List[Node]]

    def __init__(self) -> None:
        self._stack = []

    def enter(self, node: Node) -> Visit:
        if not isinstance(node, _DoccApply.FlexNode):
            self._stack.append(node)
            return Visit.TraverseChildren

        flex = node
        wrapped = flex.node

        new_node: Node

        if isinstance(wrapped, python.PythonNode):
            wrapped_py: python.PythonNode = wrapped  # Work around a mypy bug?
            assert dataclasses.is_dataclass(wrapped_py)
            arguments = {}
            offset = 0
            for field in dataclasses.fields(wrapped_py):
                if field.type == Node:
                    value = flex.children[offset]
                    offset += 1
                else:
                    value = getattr(wrapped, field.name)

                arguments[field.name] = value
            assert offset == len(flex.children)
            new_node = type(wrapped)(**arguments)
        elif isinstance(wrapped, Reference):
            assert 1 == len(flex.children)
            new_node = Reference(
                identifier=wrapped.identifier,
                child=flex.children[0],
            )
        elif isinstance(wrapped, Definition):
            assert 1 == len(flex.children)
            new_node = Definition(
                identifier=wrapped.identifier,
                specifier=wrapped.specifier,
                child=flex.children[0],
            )
        elif isinstance(wrapped, ListNode):
            new_node = ListNode(flex.children)
        elif isinstance(wrapped, mistletoe.MarkdownNode):
            new_node = mistletoe.MarkdownNode(wrapped.token)
            new_node._children = list(flex.children)
        elif isinstance(wrapped, verbatim.Transcribed):
            new_node = verbatim.Transcribed(_children=list(flex.children))
        elif isinstance(wrapped, verbatim.Line):
            new_node = verbatim.Line(
                number=wrapped.number, _children=list(flex.children)
            )
        elif isinstance(wrapped, verbatim.Highlight):
            new_node = verbatim.Highlight(
                highlights=list(wrapped.highlights),
                _children=list(flex.children),
            )
        elif isinstance(wrapped, verbatim.Text):
            new_node = verbatim.Text(text=wrapped.text)
        else:
            raise NotImplementedError(f"hardening {type(wrapped)}")

        self._stack.append(new_node)

        try:
            parent = self._stack[-2]
        except IndexError:
            return Visit.TraverseChildren

        parent.replace_child(flex, new_node)
        return Visit.TraverseChildren

    @override
    def exit(self, node: Node) -> None:
        self._stack.pop()


class _DoccApply(Apply[Node]):
    class ApplyNode(Node):
        __slots__ = ("children",)

        children: List[Node]

        def __init__(self) -> None:
            self.children = []

        def add(self, node: Node) -> None:
            self.children.append(node)

        def replace_child(self, old: Node, new: Node) -> None:
            self.children = [new if x == old else x for x in self.children]

    class FlexNode(ApplyNode):
        __slots__ = ("node",)

        node: Node

        def __init__(self, node: Node) -> None:
            super().__init__()
            self.node = node

        def __repr__(self) -> str:
            return f"FlexNode(node={self.node!r}, ...)"

    SUPPORTS_BLOCKS: Final[Tuple[Type[Node], ...]] = (
        ListNode,
        verbatim.Line,
        verbatim.Transcribed,
        verbatim.Fragment,
        verbatim.Highlight,
        verbatim.VerbatimNode,
        html.HTMLTag,
        html.HTMLRoot,
        mistletoe.MarkdownNode,
    )

    before_name: Final[str]
    after_name: Final[str]
    stack: Final[List[ApplyNode]]
    root: ApplyNode

    def __init__(
        self, before_name: str, before: Node, after_name: str, after: Node
    ) -> None:
        super().__init__(_DoccAdapter(), before, after)
        self.before_name = before_name
        self.after_name = after_name
        self.stack = []
        self.root = _DoccApply.ApplyNode()

    def apply(self, operations: Iterable[Operation]) -> None:
        assert not self.stack
        self.root.children.clear()

        try:
            self.stack.append(self.root)
            super().apply(operations)
        finally:
            self.stack.clear()

    def replace(self, befores: Sequence[Node], afters: Sequence[Node]) -> None:
        parent = self.stack[-1]
        if self._supports_blocks(parent):
            parent.add(
                DiffNode(
                    before_name=self.before_name,
                    before=BeforeNode(ListNode(list(befores))),
                    after_name=self.after_name,
                    after=AfterNode(ListNode(list(afters))),
                )
            )
        else:
            for before, after in zip_longest(befores, afters):
                parent.add(
                    DiffNode(
                        before_name=self.before_name,
                        before=BeforeNode(before) if before else BlankNode(),
                        after_name=self.after_name,
                        after=AfterNode(after) if after else BlankNode(),
                    )
                )

    def delete(self, befores: Sequence[Node]) -> None:
        parent = self.stack[-1]
        if self._supports_blocks(parent):
            parent.add(
                DiffNode(
                    before_name=self.before_name,
                    before=BeforeNode(ListNode(list(befores))),
                    after_name=self.after_name,
                    after=BlankNode(),
                )
            )
        else:
            for before in befores:
                parent.add(
                    DiffNode(
                        before_name=self.before_name,
                        before=BeforeNode(before),
                        after_name=self.after_name,
                        after=BlankNode(),
                    )
                )

    def insert(self, afters: Sequence[Node]) -> None:
        parent = self.stack[-1]
        if self._supports_blocks(parent):
            parent.add(
                DiffNode(
                    before_name=self.before_name,
                    before=BlankNode(),
                    after_name=self.after_name,
                    after=AfterNode(ListNode(list(afters))),
                )
            )
        else:
            for after in afters:
                parent.add(
                    DiffNode(
                        before_name=self.before_name,
                        before=BlankNode(),
                        after_name=self.after_name,
                        after=AfterNode(after),
                    )
                )

    @override
    def equal(self, before: Sequence[Node], after: Sequence[Node]) -> None:
        parent = self.stack[-1]
        for node in after:
            parent.add(node)

    @override
    def descend(self, before: Node, after: Node) -> None:
        parent = self.stack[-1]
        node = _DoccApply.FlexNode(after)
        parent.add(node)
        self.stack.append(node)

    def ascend(self) -> None:
        self.stack.pop()

    def output(self) -> Node:
        assert 1 == len(self.root.children)
        return self.root.children[0]

    @classmethod
    def _supports_blocks(cls: Type["_DoccApply"], node: Node) -> bool:
        candidate = node
        if isinstance(node, cls.FlexNode):
            candidate = node.node
        return isinstance(candidate, cls.SUPPORTS_BLOCKS)


class MinimizeDiffsTransform(Transform):
    """
    Move `DiffNode` nodes as far down the tree as reasonably possible.
    """

    def __init__(self, settings: PluginSettings) -> None:
        pass

    def transform(self, context: Context) -> None:
        """
        Apply the transformation to the given document.
        """
        visitor = _MinimizeDiffsVisitor()
        context[Document].root.visit(visitor)
        assert visitor.root is not None
        context[Document].root = visitor.root


class _MinimizeDiffsVisitor(Visitor):
    root: Optional[Node]
    _stack: Final[List[Node]]

    def __init__(self) -> None:
        self._stack = []
        self.root = None

    def enter(self, node: Node) -> Visit:
        self._stack.append(node)
        if self.root is None:
            self.root = node

        if not isinstance(node, DiffNode):
            return Visit.TraverseChildren

        before = node.before
        after = node.after

        if before:
            # TODO: Probably should make this work:
            assert isinstance(before, BeforeNode)
            before = before.child

        if after:
            # TODO: Probably should make this work:
            assert isinstance(after, AfterNode)
            after = after.child

        adapter = _DoccAdapter()
        matcher = TreeMatcher(adapter, before, after)
        operations = matcher.compute_operations()

        apply = _DoccApply(node.before_name, before, node.after_name, after)
        apply.apply(operations)

        apply.root.visit(_HardenVisitor())
        output = apply.output()

        if 1 == len(self._stack):
            self._stack[0] = output
            self.root = output
        else:
            self._stack[-2].replace_child(node, output)
            self._stack[-1] = output

        return Visit.SkipChildren

    @override
    def exit(self, node: Node) -> None:
        self._stack.pop()


def render_diff(
    context: object,  # noqa: U100
    parent: object,
    diff: object,
) -> html.RenderResult:
    """
    Render a DiffNode.
    """
    assert isinstance(diff, DiffNode)
    assert isinstance(parent, (html.HTMLTag, html.HTMLRoot))
    parent_: Union[html.HTMLTag, html.HTMLRoot] = parent

    if isinstance(parent_, html.HTMLTag) and parent_.tag_name == "table":
        tag = html.HTMLTag("tbody", {"class": "diff"})
    else:
        return parent_

    parent_.append(tag)
    return tag


def render_before_after(
    context: object,
    parent: object,
    node_: object,
) -> html.RenderResult:
    """
    Render a BeforeNode or an AfterNode.
    """
    assert isinstance(node_, (BeforeNode, AfterNode))
    assert isinstance(parent, (html.HTMLTag, html.HTMLRoot))
    assert isinstance(context, Context)

    node: Union[BeforeNode, AfterNode] = node_

    if isinstance(node, BeforeNode):
        tag_name = "del"
        css_class = "diff-before"
    elif isinstance(node, AfterNode):
        tag_name = "ins"
        css_class = "diff-after"
    else:
        assert_never(node)

    if isinstance(parent, html.HTMLTag) and parent.tag_name == "tbody":
        visitor = html.HTMLVisitor(context)
        node.child.visit(visitor)
        for child in visitor.root.children:
            assert isinstance(child, html.HTMLTag)
            try:
                classes = child.attributes["class"]
                if classes is None:
                    child.attributes["class"] = css_class
                else:
                    child.attributes["class"] = classes + " " + css_class
            except KeyError:
                child.attributes["class"] = css_class

            parent.append(child)
        return None
    else:
        div = html.HTMLTag(tag_name, {"class": css_class})
        parent.append(div)
        return div
