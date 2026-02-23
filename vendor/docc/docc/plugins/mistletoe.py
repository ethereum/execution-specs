# Copyright (C) 2022-2024 Ethereum Foundation
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
Markdown support for docc.
"""

from typing import (
    Callable,
    Final,
    Iterable,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Union,
    runtime_checkable,
)

import mistletoe as md
from mistletoe import block_token as blocks
from mistletoe import span_token as spans
from mistletoe.token import Token as MarkdownToken
from typing_extensions import TypeAlias

from docc.context import Context
from docc.document import Document, ListNode, Node, Visit, Visitor
from docc.plugins import html, python, references, search
from docc.settings import PluginSettings
from docc.transform import Transform


class MarkdownNode(Node, search.Searchable):
    """
    Representation of a markdown node.
    """

    __slots__ = ("token", "_children")

    token: Final[MarkdownToken]
    _children: Optional[List[Node]]

    def __init__(self, token: MarkdownToken) -> None:
        self.token = token
        self._children = None

    @property
    def children(self) -> Iterable[Node]:
        """
        Child nodes belonging to this node.
        """
        current = self._children
        if current is not None:
            return current

        children = getattr(self.token, "children", tuple())
        if children is None:
            children = tuple()
        replacement: List[Node] = [MarkdownNode(c) for c in children]
        self._children = replacement
        return replacement

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old node with the given new node.
        """
        self._children = [new if x == old else x for x in self.children]

    def to_search(self) -> search.Content:
        """
        Extract the text from this node to put in the search index.
        """
        return " ".join(_SearchVisitor.collect(self))

    def search_children(self) -> bool:
        """
        `True` if the children of this node should be searched, `False`
        otherwise.
        """
        return False


class DocstringTransform(Transform):
    """
    Replaces python docstring nodes with markdown nodes.
    """

    def __init__(self, config: PluginSettings) -> None:
        """
        Create a Transform with the given configuration.
        """

    def transform(self, context: Context) -> None:
        """
        Apply the transformation to the given document.
        """
        visitor = _DocstringVisitor()
        context[Document].root.visit(visitor)
        assert visitor.root is not None
        context[Document].root = visitor.root


class _DocstringVisitor(Visitor):
    root: Optional[Node]
    stack: Final[List[Node]]

    def __init__(self) -> None:
        self.stack = []
        self.root = None

    def enter(self, node: Node) -> Visit:
        self.stack.append(node)
        if self.root is None:
            self.root = node
        return Visit.TraverseChildren

    def exit(self, node: Node) -> None:
        popped = self.stack.pop()
        assert node == popped

        if not isinstance(node, python.Docstring):
            return

        document = md.Document(node.text)
        new_node = MarkdownNode(document)

        if self.stack:
            self.stack[-1].replace_child(node, new_node)
        else:
            self.root = new_node


class ReferenceTransform(Transform):
    """
    Replaces markdown link and autolink nodes with [`Reference`] nodes instead.

    [`Reference`]: ref:docc.plugins.references.Reference
    """

    def __init__(self, config: PluginSettings) -> None:
        """
        Create a Transform with the given configuration.
        """

    def transform(self, context: Context) -> None:
        """
        Apply the transformation to the given document.
        """
        visitor = _ReferenceVisitor()
        context[Document].root.visit(visitor)
        assert visitor.root is not None
        context[Document].root = visitor.root


class _ReferenceVisitor(Visitor):
    root: Optional[Node]
    stack: Final[List[Node]]

    def __init__(self) -> None:
        self.stack = []
        self.root = None

    def enter(self, node: Node) -> Visit:
        self.stack.append(node)
        if self.root is None:
            self.root = node
        return Visit.TraverseChildren

    def exit(self, node: Node) -> None:
        popped = self.stack.pop()
        assert node == popped

        if not isinstance(node, MarkdownNode):
            return

        token = node.token
        if not isinstance(token, (spans.Link, spans.AutoLink)):
            return

        ref = token.target.removeprefix("ref:")
        if ref == token.target:
            return

        new_node = references.Reference(ref)

        children = list(node.children)
        if len(children) == 1:
            new_node.child = children[0]
        elif len(children) > 1:
            new_node.child = ListNode(children)

        if self.stack:
            self.stack[-1].replace_child(node, new_node)
        else:
            self.root = new_node


def _render_strong(
    context: Context,
    parent: html.HTMLRoot | html.HTMLTag,
    node: MarkdownNode,
) -> html.RenderResult:
    tag = html.HTMLTag("strong")
    parent.append(tag)
    return tag


def _render_emphasis(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    tag = html.HTMLTag("em")
    parent.append(tag)
    return tag


def _render_inline_code(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    tag = html.HTMLTag("code")
    parent.append(tag)
    return tag


def _render_raw_text(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    token = node.token
    assert isinstance(token, spans.RawText)
    parent.append(html.TextNode(token.content))
    return None


def _render_strikethrough(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    tag = html.HTMLTag("del")
    parent.append(tag)
    return tag


def _render_image(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    token = node.token
    assert isinstance(token, spans.Image)
    attributes = {
        "src": token.src,
        "alt": token.content,
    }
    if token.title:
        attributes["title"] = token.title
    tag = html.HTMLTag("img", attributes)
    parent.append(tag)
    return None


def _render_link(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    token = node.token
    assert isinstance(token, spans.Link)
    attributes = {"href": token.target}
    if token.title:
        attributes["title"] = token.title
    tag = html.HTMLTag("a", attributes)
    parent.append(tag)
    return tag


def _render_auto_link(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    token = node.token
    assert isinstance(token, spans.AutoLink)
    if token.mailto:
        href = f"mailto:{token.target}"
    else:
        href = token.target
    attributes = {"href": href}
    tag = html.HTMLTag("a", attributes)
    parent.append(tag)
    return tag


def _render_escape_sequence(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    raise NotImplementedError()


def _render_heading(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    token = node.token
    assert isinstance(token, (blocks.Heading, blocks.SetextHeading))
    tag = html.HTMLTag(f"h{token.level}")
    parent.append(tag)
    return tag


def _render_quote(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    # TODO: Understand what mistletoe's ptag stack is for.
    token = node.token
    assert isinstance(token, blocks.Quote)
    tag = html.HTMLTag("blockquote")
    parent.append(tag)
    return tag


def _render_paragraph(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    # TODO: Understand what mistletoe's ptag stack is for.
    token = node.token
    assert isinstance(token, blocks.Paragraph)
    tag = html.HTMLTag("p")
    parent.append(tag)
    return tag


def _render_block_code(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    pre = html.HTMLTag("pre")
    code = html.HTMLTag("code")
    pre.append(code)
    parent.append(pre)
    return code


def _render_list(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    # TODO: Understand what mistletoe's ptag stack is for.
    token = node.token
    assert isinstance(token, blocks.List)
    if token.start is None:
        tag = html.HTMLTag("ul")
    else:
        attributes = {}
        if token.start != 1:
            attributes["start"] = token.start
        tag = html.HTMLTag("ol", attributes)
    parent.append(tag)
    return tag


def _render_list_item(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    # TODO: Understand what mistletoe's ptag stack is for.
    token = node.token
    assert isinstance(token, blocks.ListItem)
    tag = html.HTMLTag("li")
    parent.append(tag)
    return tag


@runtime_checkable
class _TableWithHeader(Protocol):
    header: MarkdownToken


def _render_table(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    # TODO: mistletoe had a much more complicated implementation.
    table = html.HTMLTag("table")
    token = node.token

    if isinstance(token, _TableWithHeader):
        # TODO: The table header should appear in node's `.children`.
        header_node = MarkdownNode(token.header)

        visitor = html.HTMLVisitor(context)
        header_node.visit(visitor)

        thead = html.HTMLTag("thead")
        for node in visitor.root.children:
            thead.append(node)
        table.append(thead)

    parent.append(table)
    return table


def _render_table_row(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    # TODO: mistletoe had a much more complicated implementation.
    row = html.HTMLTag("tr")
    parent.append(row)
    return row


def _render_table_cell(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    # TODO: mistletoe had a much more complicated implementation.
    token = node.token
    assert isinstance(token, blocks.TableCell)
    if token.align is None:
        align = "left"
    elif token.align == 0:
        align = "center"
    elif token.align == 2:
        align = "right"
    else:
        raise NotImplementedError(f"table alignment {token.align}")
    cell = html.HTMLTag("td", {"align": align})
    parent.append(cell)
    return cell


def _render_thematic_break(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    parent.append(html.HTMLTag("hr"))
    return None


def _render_line_break(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    token = node.token
    assert isinstance(token, spans.LineBreak)
    tag = html.TextNode("\n") if token.soft else html.HTMLTag("br")
    parent.append(tag)
    return None


def _render_html_span(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    token = node.token
    assert isinstance(token, spans.HTMLSpan)
    parser = html.HTMLParser(context)
    parser.feed(token.content)
    for child in parser.root.children:
        parent.append(child)
    return None


def _render_html_block(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    token = node.token
    assert isinstance(token, blocks.HTMLBlock)
    parser = html.HTMLParser(context)
    parser.feed(token.content)
    for child in parser.root.children:
        parent.append(child)
    return None


def _render_document(
    context: Context,
    parent: Union[html.HTMLRoot, html.HTMLTag],
    node: MarkdownNode,
) -> html.RenderResult:
    # TODO: footnotes?
    token = node.token
    assert isinstance(token, blocks.Document)
    tag = html.HTMLTag("div", {"class": "markdown"})
    parent.append(tag)
    return tag


_RENDER_FUNC: TypeAlias = Callable[
    [Context, Union[html.HTMLRoot, html.HTMLTag], MarkdownNode],
    html.RenderResult,
]

_RENDERERS: Mapping[str, _RENDER_FUNC] = {
    "Strong": _render_strong,
    "Emphasis": _render_emphasis,
    "InlineCode": _render_inline_code,
    "RawText": _render_raw_text,
    "Strikethrough": _render_strikethrough,
    "Image": _render_image,
    "Link": _render_link,
    "AutoLink": _render_auto_link,
    "EscapeSequence": _render_escape_sequence,
    "Heading": _render_heading,
    "SetextHeading": _render_heading,
    "Quote": _render_quote,
    "Paragraph": _render_paragraph,
    "CodeFence": _render_block_code,
    "BlockCode": _render_block_code,
    "List": _render_list,
    "ListItem": _render_list_item,
    "Table": _render_table,
    "TableRow": _render_table_row,
    "TableCell": _render_table_cell,
    "ThematicBreak": _render_thematic_break,
    "LineBreak": _render_line_break,
    "Document": _render_document,
    "HTMLBlock": _render_html_block,
    "HTMLSpan": _render_html_span,
}


def render_html(
    context: object,
    parent: object,
    node: object,
) -> html.RenderResult:
    """
    Render a markdown node as HTML.
    """
    assert isinstance(context, Context)
    assert isinstance(parent, (html.HTMLRoot, html.HTMLTag))
    assert isinstance(node, MarkdownNode)

    return _RENDERERS[node.token.__class__.__name__](context, parent, node)


class _SearchVisitor(Visitor):
    texts: List[str]

    @staticmethod
    def collect(nodes: Union[Node, Sequence[Node]]) -> List[str]:
        if isinstance(nodes, Node):
            nodes = [nodes]

        visitor = _SearchVisitor()

        for node in nodes:
            node.visit(visitor)

        return visitor.texts

    def __init__(self) -> None:
        self.texts = []

    def enter(self, node: Node) -> Visit:
        # TODO: Doesn't consider non-markdown nodes or HTML correctly.
        if not isinstance(node, MarkdownNode):
            return Visit.TraverseChildren

        token = node.token
        if isinstance(token, spans.RawText):
            self.texts.append(token.content)
            return Visit.SkipChildren
        return Visit.TraverseChildren

    def exit(self, node: Node) -> None:
        pass
