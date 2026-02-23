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
Rendering functions to transform Python nodes into HTML.
"""

from docc.context import Context
from docc.document import Node
from docc.plugins.html import (
    HTMLRoot,
    HTMLTag,
    RenderResult,
    TextNode,
    render_template,
)

from . import nodes


def _render_template(
    context: object, parent: object, template_name: str, node: Node
) -> RenderResult:
    assert isinstance(context, Context)
    assert isinstance(parent, (HTMLTag, HTMLRoot))
    return render_template(
        "docc.plugins.python", context, parent, template_name, node
    )


def render_module(
    context: object,
    parent: object,
    module: object,
) -> RenderResult:
    """
    Render a python Module as HTML.
    """
    assert isinstance(module, nodes.Module)
    return _render_template(context, parent, "html/module.html", module)


def render_class(
    context: object,
    parent: object,
    class_: object,
) -> RenderResult:
    """
    Render a python Class as HTML.
    """
    assert isinstance(class_, nodes.Class)
    return _render_template(context, parent, "html/class.html", class_)


def render_attribute(
    context: object,
    parent: object,
    attribute: object,
) -> RenderResult:
    """
    Render a python assignment as HTML.
    """
    assert isinstance(attribute, nodes.Attribute)
    return _render_template(context, parent, "html/attribute.html", attribute)


def render_function(
    context: object,
    parent: object,
    function: object,
) -> RenderResult:
    """
    Render a python Function as HTML.
    """
    assert isinstance(function, nodes.Function)
    return _render_template(context, parent, "html/function.html", function)


def render_access(
    context: object,
    parent: object,
    access: object,
) -> RenderResult:
    """
    Render a python Access as HTML.
    """
    assert isinstance(access, nodes.Access)
    return _render_template(context, parent, "html/access.html", access)


def render_name(
    context: object,
    parent: object,
    name: object,
) -> RenderResult:
    """
    Render a python Name as HTML.
    """
    assert isinstance(name, nodes.Name)
    return _render_template(context, parent, "html/name.html", name)


def render_type(
    context: object,
    parent: object,
    type_: object,
) -> RenderResult:
    """
    Render a python Type as HTML.
    """
    assert isinstance(type_, nodes.Type)
    return _render_template(context, parent, "html/type.html", type_)


def render_list(
    context: object,
    parent: object,
    list_: object,
) -> RenderResult:
    """
    Render a python List as HTML.
    """
    assert isinstance(list_, nodes.List)
    return _render_template(context, parent, "html/list.html", list_)


def render_tuple(
    context: object,
    parent: object,
    tuple_: object,
) -> RenderResult:
    """
    Render a python List as HTML.
    """
    assert isinstance(tuple_, nodes.Tuple)
    return _render_template(context, parent, "html/tuple.html", tuple_)


def render_docstring(
    context: object,
    parent: object,
    docstring: object,
) -> RenderResult:
    """
    Render a python Docstring as HTML.
    """
    assert isinstance(docstring, nodes.Docstring)
    assert isinstance(parent, (HTMLRoot, HTMLTag))
    parent.append(TextNode(docstring.text))
    return None


def render_parameter(
    context: object,
    parent: object,
    parameter: object,
) -> RenderResult:
    """
    Render a python Parameter as HTML.
    """
    assert isinstance(parameter, nodes.Parameter)
    return _render_template(context, parent, "html/parameter.html", parameter)


def render_subscript(
    context: object,
    parent: object,
    subscript: object,
) -> RenderResult:
    """
    Render a python Subscript as HTML.
    """
    assert isinstance(subscript, nodes.Subscript)
    return _render_template(context, parent, "html/subscript.html", subscript)


def render_binary_operation(
    context: object,
    parent: object,
    binary: object,
) -> RenderResult:
    """
    Render a python BinaryOperation as HTML.
    """
    assert isinstance(binary, nodes.BinaryOperation)
    return _render_template(
        context, parent, "html/binary_operation.html", binary
    )


def render_bit_or(
    context: object,
    parent: object,
    bit_or: object,
) -> RenderResult:
    """
    Render a python BitOr as HTML.
    """
    assert isinstance(bit_or, nodes.BitOr)
    return _render_template(context, parent, "html/bit_or.html", bit_or)
