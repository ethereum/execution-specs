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
Rendering functions to transform verbatim nodes into HTML.
"""

from docc.context import Context
from docc.plugins.html import HTMLRoot, HTMLTag, RenderResult, TextNode

from . import Highlight, Line, Text, Transcribed


def render_transcribed(
    context: Context,
    parent: object,
    node: object,
) -> RenderResult:
    """
    Render a transcribed block as HTML.
    """
    assert isinstance(context, Context)
    assert isinstance(parent, (HTMLRoot, HTMLTag))
    assert isinstance(node, Transcribed)

    table = HTMLTag("table", attributes={"class": "verbatim"})
    parent.append(table)
    return table


def render_line(
    context: Context,
    parent: object,
    node: object,
) -> RenderResult:
    """
    Render a transcribed line as HTML.
    """
    assert isinstance(context, Context)
    assert isinstance(parent, (HTMLRoot, HTMLTag))
    assert isinstance(node, Line)

    line_text = TextNode(str(node.number))

    line_cell = HTMLTag("th")
    line_cell.append(line_text)

    code_pre = HTMLTag("pre")

    code_cell = HTMLTag("td")
    code_cell.append(code_pre)

    row = HTMLTag("tr")
    row.append(line_cell)
    row.append(code_cell)

    if isinstance(parent, HTMLTag) and parent.tag_name.casefold() == "table":
        tbody = HTMLTag("tbody")
        tbody.append(row)
        parent.append(tbody)
    else:
        parent.append(row)
    return code_pre


def render_text(
    context: Context,
    parent: object,
    node: object,
) -> RenderResult:
    """
    Render transcribed text as HTML.
    """
    assert isinstance(context, Context)
    assert isinstance(parent, (HTMLRoot, HTMLTag))
    assert isinstance(node, Text)

    parent.append(TextNode(node.text))
    return None


def render_highlight(
    context: Context,
    parent: object,
    node: object,
) -> RenderResult:
    """
    Render transcribed text as HTML.
    """
    assert isinstance(context, Context)
    assert isinstance(parent, (HTMLRoot, HTMLTag))
    assert isinstance(node, Highlight)

    classes = [f"hi-{h}" for h in node.highlights] + ["hi"]
    new_node = HTMLTag(
        "span",
        attributes={
            "class": " ".join(classes),
        },
    )
    parent.append(new_node)
    return new_node
