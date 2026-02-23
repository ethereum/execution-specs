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
Documentation plugin for Python.
"""

import glob
import logging
import os.path
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from pathlib import PurePath
from textwrap import dedent
from typing import (
    Dict,
    Final,
    FrozenSet,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    TextIO,
    Tuple,
    Type,
)

import libcst as cst
from inflection import dasherize, underscore
from libcst.metadata import ExpressionContext
from typing_extensions import assert_never

from docc.build import Builder
from docc.context import Context
from docc.discover import Discover, T
from docc.document import BlankNode, Document, ListNode, Node, Visit, Visitor
from docc.plugins.references import Definition, Reference
from docc.plugins.verbatim import Fragment, Pos, Verbatim
from docc.settings import PluginSettings
from docc.source import Source, TextSource
from docc.transform import Transform

from . import nodes

WHITESPACE: Tuple[Type[cst.CSTNode], ...] = (
    cst.TrailingWhitespace,
    cst.EmptyLine,
    cst.SimpleWhitespace,
    cst.ParenthesizedWhitespace,
    cst.Newline,
)
"""
libcst nodes that count as whitespace and should be ignored.
"""


class PythonDiscover(Discover):
    """
    Find Python source files.
    """

    paths: Sequence[str]
    """
    File system paths to search for Python files.
    """

    excluded_paths: Final[Sequence[PurePath]]
    """
    File system paths to exclude from the search. Excluding a parent directory
    excludes all children.
    """

    settings: PluginSettings

    def __init__(self, config: PluginSettings) -> None:
        self.settings = config

        paths = config.get("paths", [])
        if not isinstance(paths, Sequence):
            raise TypeError("python paths must be a list")

        if any(not isinstance(path, str) for path in paths):
            raise TypeError("every python path must be a string")

        if not paths:
            raise ValueError("python needs at least one path")

        self.paths = [str(config.resolve_path(path)) for path in paths]

        excluded_paths = config.get("excluded_paths", [])
        if not isinstance(excluded_paths, Sequence):
            raise TypeError("python excluded paths must be a list")

        if any(not isinstance(path, str) for path in excluded_paths):
            raise TypeError("every python path must be a string")

        self.excluded_paths = [PurePath(p) for p in excluded_paths]

    def discover(self, known: FrozenSet[T]) -> Iterator[Source]:
        """
        Find sources.
        """
        escaped = ((path, glob.escape(path)) for path in self.paths)
        joined = ((r, os.path.join(pat, "**", "*.py")) for r, pat in escaped)
        globbed = ((r, glob.glob(pat, recursive=True)) for r, pat in joined)

        for root_text, absolute_texts in globbed:
            root_path = PurePath(root_text)
            for absolute_text in absolute_texts:
                absolute_path = PurePath(absolute_text)
                relative_path = self.settings.unresolve_path(absolute_path)

                parents = relative_path.parents
                if not any(p in parents for p in self.excluded_paths):
                    yield PythonSource(root_path, relative_path, absolute_path)


class PythonSource(TextSource):
    """
    A Source representing a Python file.
    """

    root_path: Final[PurePath]
    absolute_path: Final[PurePath]
    _relative_path: Final[PurePath]

    def __init__(
        self,
        root_path: PurePath,
        relative_path: PurePath,
        absolute_path: PurePath,
    ) -> None:
        self.root_path = root_path
        self._relative_path = relative_path
        self.absolute_path = absolute_path

    @property
    def relative_path(self) -> Optional[PurePath]:
        """
        The relative path to the Source.
        """
        return self._relative_path

    @property
    def output_path(self) -> PurePath:
        """
        Where to put the output derived from this source.
        """
        return self._relative_path

    def open(self) -> TextIO:
        """
        Open the source for reading.
        """
        return open(self.absolute_path, "r")


class PythonBuilder(Builder):
    """
    Convert python source files into syntax trees.
    """

    settings: PluginSettings

    def __init__(self, config: PluginSettings) -> None:
        """
        Create a PythonBuilder with the given configuration.
        """
        self.settings = config

    def build(
        self,
        unprocessed: Set[Source],
        processed: Dict[Source, Document],
    ) -> None:
        """
        Consume unprocessed Sources and insert their Documents into processed.
        """
        source_set = set(s for s in unprocessed if isinstance(s, PythonSource))
        unprocessed -= source_set

        all_modules = set()

        sources_by_root = defaultdict(set)
        for source in source_set:
            root = self.settings.resolve_path(source.root_path)
            sources_by_root[root].add(source)

        for root, sources in sources_by_root.items():
            paths = set()

            for source in sources:
                if source.relative_path is None:
                    continue
                abs_path = self.settings.resolve_path(source.relative_path)
                paths.add(str(abs_path))

            repo_manager = cst.metadata.FullRepoManager(
                repo_root_dir=str(root),
                paths=list(paths),
                providers=_CstVisitor.METADATA_DEPENDENCIES,
            )

            for source in sources:
                assert source.relative_path
                abs_path = self.settings.resolve_path(source.relative_path)

                visitor = _CstVisitor(all_modules, source)
                repo_manager.get_metadata_wrapper_for_path(
                    str(abs_path)
                ).visit(visitor)
                assert visitor.root is not None

                document = Document(
                    visitor.root,
                )

                processed[source] = document


class CstNode(Node):
    """
    A python concrete syntax tree node.
    """

    cst_node: cst.CSTNode
    source: Source
    _children: List[Node]
    start: Pos
    end: Pos
    type: Optional[str]
    global_scope: Optional[bool]
    class_scope: Optional[bool]
    expression_context: Optional[ExpressionContext]
    names: Set[str]
    all_modules: Set[str]  # TODO: Make this a FrozenSet

    def __init__(
        self,
        all_modules: Set[str],
        cst_node: cst.CSTNode,
        source: Source,
        start: Pos,
        end: Pos,
        type_: Optional[str],
        global_scope: Optional[bool],
        class_scope: Optional[bool],
        expression_context: Optional[ExpressionContext],
        names: Set[str],
        children: List[Node],
    ) -> None:
        self.all_modules = all_modules
        self.cst_node = cst_node
        self.source = source
        self._children = children
        self.start = start
        self.end = end
        self.type = type_
        self.global_scope = global_scope
        self.class_scope = class_scope
        self.expression_context = expression_context
        self.names = names

    @property
    def children(self) -> Sequence[Node]:
        """
        Child nodes belonging to this node.
        """
        return self._children

    def replace_child(self, old: Node, new: Node) -> None:
        """
        Replace the old node with the given new node.
        """
        self._children = [new if c == old else c for c in self.children]

    def find_child(self, cst_node: cst.CSTNode) -> Node:
        """
        Given a libcst node, find the CstNode in the same position.
        """
        index = self.cst_node.children.index(cst_node)
        return self.children[index]

    def __repr__(self) -> str:
        """
        Textual representation of this instance.
        """
        cst_node = self.cst_node
        text = f"{self.__class__.__name__}({cst_node.__class__.__name__}(...)"
        text += f", start={self.start}"
        text += f", end={self.end}"
        if self.type is not None:
            text += f", type={self.type!r}"
        if self.names:
            text += f", names={self.names!r}"
        return text + ")"


class _CstVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (
        cst.metadata.PositionProvider,
        cst.metadata.FullyQualifiedNameProvider,
        # cst.metadata.TypeInferenceProvider,
        cst.metadata.ScopeProvider,
        cst.metadata.ExpressionContextProvider,
    )

    stack: Final[List[CstNode]]
    source: Final[Source]
    all_modules: Final[Set[str]]
    root: Optional[CstNode]

    def __init__(self, all_modules: Set[str], source: Source) -> None:
        super().__init__()
        self.stack = []
        self.root = None
        self.source = source
        self.all_modules = all_modules

    def on_visit(self, node: cst.CSTNode) -> bool:
        try:
            position = self.get_metadata(cst.metadata.PositionProvider, node)
        except KeyError:
            return True

        type_ = None  # self.get_metadata(
        #    cst.metadata.TypeInferenceProvider, node, None
        # )

        scope = self.get_metadata(cst.metadata.ScopeProvider, node, None)
        global_scope = isinstance(scope, cst.metadata.GlobalScope)
        class_scope = isinstance(scope, cst.metadata.ClassScope)

        expression_context = self.get_metadata(
            cst.metadata.ExpressionContextProvider, node, None
        )

        qualified_names = self.get_metadata(
            cst.metadata.FullyQualifiedNameProvider, node, None
        )
        names: Set[str] = set()
        if qualified_names:
            names = set(n.name for n in qualified_names)

        start = Pos(
            line=position.start.line,
            column=position.start.column,
        )
        end = Pos(
            line=position.end.line,
            column=position.end.column,
        )
        new = CstNode(
            self.all_modules,
            node,
            self.source,
            start,
            end,
            type_,
            global_scope,
            class_scope,
            expression_context,
            names,
            [],
        )

        if self.stack:
            self.stack[-1]._children.append(new)
        else:
            assert self.root is None

        if self.root is None:
            self.root = new

        if isinstance(node, cst.Module):
            self.all_modules.update(names)

        self.stack.append(new)
        return True

    def on_leave(self, original_node: cst.CSTNode) -> None:
        try:
            self.get_metadata(cst.metadata.PositionProvider, original_node)
        except KeyError:
            return
        self.stack.pop()


class PythonTransform(Transform):
    """
    Transforms CstNode instances into Python language nodes.
    """

    excluded_references: Final[FrozenSet[str]]

    def __init__(self, config: PluginSettings) -> None:
        """
        Create a Transform with the given configuration.
        """
        self.excluded_references = frozenset(
            config.get("excluded_references", [])
        )

    def transform(self, context: Context) -> None:
        """
        Apply the transformation to the given document.
        """
        document = context[Document]

        document.root.visit(
            _AnnotationReferenceTransformVisitor(self.excluded_references)
        )

        visitor = _ReplaceVisitor(context)
        document.root.visit(visitor)

        document.root.visit(_AnnotationTransformVisitor())
        document.root.visit(_NameTransformVisitor())


class _ReplaceVisitor(Visitor):
    context: Final[Context]
    parents: Final[List[Node]]

    def __init__(self, context: Context) -> None:
        super().__init__()
        self.parents = []
        self.context = context

    def _replace_child(self, old: Node, new: Node) -> None:
        if self.parents:
            self.parents[-1].replace_child(old, new)
        else:
            document = self.context[Document]
            assert document.root == old
            document.root = new

    def enter(self, node: Node) -> Visit:
        if not isinstance(node, CstNode):
            self.parents.append(node)
            return Visit.TraverseChildren

        transformer = _TransformVisitor(self.context)

        node.visit(transformer)
        assert transformer.root is not None

        self._replace_child(node, transformer.root)
        return Visit.SkipChildren

    def exit(self, node: Node) -> None:
        if not isinstance(node, CstNode):
            popped = self.parents.pop()
            assert popped == node


@dataclass
class _TransformContext:
    node: "CstNode"
    child_offset: int = 0


class _TransformVisitor(Visitor):
    root: Optional[Node]
    old_stack: Final[List[_TransformContext]]
    new_stack: Final[List[Node]]
    context: Final[Context]
    document: Final[Document]

    def __init__(self, context: Context) -> None:
        self.root = None
        self.old_stack = []
        self.new_stack = []
        self.document = context[Document]
        self.context = context

    def push_new(self, node: Node) -> None:
        if self.root is None:
            assert 0 == len(self.new_stack)
            self.root = node
        self.new_stack.append(node)

    def enter_module(self, node: CstNode, cst_node: cst.Module) -> Visit:
        assert 0 == len(self.new_stack)
        module = nodes.Module()

        names = sorted(node.names)

        if names:
            module.name = nodes.Name(names[0], names[0])

        maybe_definition: Node = module
        for name in names:
            maybe_definition = Definition(
                identifier=name, child=maybe_definition
            )
            self.push_new(maybe_definition)

        self.push_new(module)

        docstring = cst_node.get_docstring(True)
        if docstring is not None:
            module.docstring = nodes.Docstring(docstring)

        return Visit.TraverseChildren

    def exit_module(self, node: CstNode) -> None:
        self.new_stack.pop()
        for _name in node.names:
            self.new_stack.pop()

    def enter_class_def(self, node: CstNode, cst_node: cst.ClassDef) -> Visit:
        assert 0 < len(self.new_stack)

        class_def = nodes.Class()
        self.push_new(class_def)

        docstring = cst_node.get_docstring(True)
        if docstring is not None:
            class_def.docstring = nodes.Docstring(docstring)

        class_def.name = node.find_child(cst_node.name)

        source = node.source
        if isinstance(source, TextSource):
            assert isinstance(class_def.decorators, ListNode)
            decorators = class_def.decorators.children
            for cst_decorator in cst_node.decorators:
                decorator = node.find_child(cst_decorator)

                # Trim whitespace from each decorator.
                if isinstance(decorator, CstNode):
                    decorator = decorator.find_child(cst_decorator.decorator)

                decorators.append(_VerbatimTransform.apply(source, decorator))

        maybe_definition: Node = class_def
        for name in node.names:
            maybe_definition = Definition(
                identifier=name, child=maybe_definition
            )

        if 1 < len(self.new_stack):
            parent = self.new_stack[-2]
            members = getattr(parent, "members", None)
            if isinstance(members, ListNode):
                members.children.append(maybe_definition)

        body = node.find_child(cst_node.body)
        assert isinstance(body, CstNode)

        class_context = _TransformContext(node=node)
        body_context = _TransformContext(node=body)

        self.old_stack.append(class_context)
        self.old_stack.append(body_context)

        for index, cst_statement in enumerate(cst_node.body.body):
            self.old_stack[-1].child_offset = index
            if isinstance(cst_statement, cst.SimpleStatementLine):
                if len(cst_statement.body) == 1:
                    cst_first = cst_statement.body[0]
                    if isinstance(cst_first, cst.Expr):
                        if isinstance(cst_first.value, cst.SimpleString):
                            continue
            statement = body.find_child(cst_statement)
            statement.visit(self)

        popped = self.old_stack.pop()
        assert popped == body_context

        popped = self.old_stack.pop()
        assert popped == class_context

        # TODO: base classes
        # TODO: metaclass

        return Visit.SkipChildren

    def exit_class_def(self) -> None:
        self.new_stack.pop()

    def enter_function_def(
        self, node: CstNode, cst_node: cst.FunctionDef
    ) -> Visit:
        assert 0 < len(self.new_stack)

        parameters = []
        function_def = nodes.Function(
            asynchronous=cst_node.asynchronous is not None,
            parameters=ListNode(parameters),
        )
        self.push_new(function_def)

        docstring = cst_node.get_docstring(True)
        if docstring is not None:
            function_def.docstring = nodes.Docstring(docstring)

        function_def.name = node.find_child(cst_node.name)

        if cst_node.returns is not None:
            function_def.return_type = node.find_child(cst_node.returns)

        source = node.source
        if isinstance(source, TextSource):
            body = node.find_child(cst_node.body)
            function_def.body = _VerbatimTransform.apply(source, body)

            assert isinstance(function_def.decorators, ListNode)
            decorators = function_def.decorators.children
            for cst_decorator in cst_node.decorators:
                decorator = node.find_child(cst_decorator)

                # Trim whitespace from each decorator.
                if isinstance(decorator, CstNode):
                    decorator = decorator.find_child(cst_decorator.decorator)

                decorators.append(_VerbatimTransform.apply(source, decorator))

        maybe_definition: Node = function_def
        for name in node.names:
            maybe_definition = Definition(
                identifier=name, child=maybe_definition
            )

        if 1 < len(self.new_stack):
            parent = self.new_stack[-2]
            members = getattr(parent, "members", None)
            if isinstance(members, ListNode):
                members.children.append(maybe_definition)

        for param in node.find_child(cst_node.params).children:
            if not isinstance(param, CstNode):
                parameters.append(param)
                continue

            parameter = nodes.Parameter()
            parameters.append(parameter)

            cst_param = param.cst_node
            if isinstance(cst_param, cst.Param):
                parameter.name = param.find_child(cst_param.name)
                if cst_param.star == "*":
                    parameter.star = "*"
                elif cst_param.star == "**":
                    parameter.star = "**"

                if cst_param.annotation is not None:
                    parameter.type_annotation = param.find_child(
                        cst_param.annotation
                    )

                if cst_param.default is not None:
                    # TODO: parameter default
                    logging.warning("parameter default values not implemented")
            elif isinstance(cst_param, cst.ParamSlash):
                parameter.name = nodes.Name("/")
            elif isinstance(cst_param, cst.ParamStar):
                parameter.name = nodes.Name("*")
            else:
                raise NotImplementedError(f"parameter type `{param}`")

        return Visit.SkipChildren

    def exit_function_def(self) -> None:
        self.new_stack.pop()

    def _assign_docstring(self) -> Optional[nodes.Docstring]:
        parent_context = self.old_stack[-1]
        parent = parent_context.node
        if not isinstance(parent, CstNode):
            return None

        cst_parent = parent.cst_node
        if not isinstance(cst_parent, cst.SimpleStatementLine):
            return None

        try:
            line_parent_context = self.old_stack[-2]
            if isinstance(line_parent_context.node.cst_node, cst.Module):
                sibling_index = line_parent_context.child_offset + 1
            else:
                sibling_index = line_parent_context.child_offset + 2
            sibling = line_parent_context.node.children[sibling_index]
        except IndexError:
            return None

        if not isinstance(sibling, CstNode):
            return None

        cst_sibling = sibling.cst_node
        if not isinstance(cst_sibling, cst.SimpleStatementLine):
            return None

        if len(cst_sibling.body) != 1:
            return None

        cst_body = cst_sibling.body[0]

        if not isinstance(cst_body, cst.Expr):
            return None

        cst_value = cst_body.value

        if not isinstance(cst_value, cst.SimpleString):
            return None

        value = cst_value.evaluated_value
        if isinstance(value, str):
            text = value
        elif isinstance(value, bytes):
            text = value.decode(encoding="utf-8", errors="strict")
        else:
            assert_never(value)
            raise AssertionError()

        text = dedent(text)
        return nodes.Docstring(text=text)

    def _enter_assignment(
        self,
        node: CstNode,
        targets: Sequence[Node],
        value: Optional[Node],
    ) -> Visit:
        if not node.global_scope and not node.class_scope:
            return Visit.SkipChildren

        if not self.new_stack:
            return Visit.SkipChildren

        parent = self.new_stack[-1]
        members = getattr(parent, "members", None)
        if not isinstance(members, ListNode):
            return Visit.SkipChildren

        names: List[Node] = []
        attribute = nodes.Attribute(names=ListNode(names))

        docstring = self._assign_docstring()
        if docstring:
            attribute.docstring = docstring

        for target in targets:
            names.append(deepcopy(target))

        source = node.source
        if isinstance(source, TextSource):
            attribute.body = _VerbatimTransform.apply(source, node)

        maybe_definition = attribute
        for name_node in names:
            if not isinstance(name_node, CstNode):
                continue

            for name in name_node.names:
                maybe_definition = Definition(
                    identifier=name, child=maybe_definition
                )

        members.children.append(maybe_definition)
        return Visit.SkipChildren

    def enter_ann_assign(
        self, node: CstNode, cst_node: cst.AnnAssign
    ) -> Visit:
        value = None
        if cst_node.value is not None:
            value = node.find_child(cst_node.value)
        return self._enter_assignment(
            node,
            [node.find_child(cst_node.target)],
            value,
        )

    def exit_ann_assign(self) -> None:
        pass

    def enter_assign(self, node: CstNode, cst_node: cst.Assign) -> Visit:
        targets = []
        for cst_target in cst_node.targets:
            target = node.find_child(cst_target)
            assert isinstance(target, CstNode)  # TODO: Assumes only CstNodes.
            targets.append(target.find_child(cst_target.target))

        return self._enter_assignment(
            node,
            targets,
            node.find_child(cst_node.value),
        )

    def exit_assign(self) -> None:
        pass

    def enter(self, node: Node) -> Visit:
        if not isinstance(node, CstNode):
            raise ValueError(
                "expected `"
                + CstNode.__name__
                + "` but got `"
                + node.__class__.__name__
                + "`"
            )

        cst_node = node.cst_node
        try:
            parent = self.old_stack[-1].node.cst_node
        except IndexError:
            parent = None

        module_member = isinstance(parent, cst.Module)

        visit: Visit

        if isinstance(cst_node, cst.Module):
            visit = self.enter_module(node, cst_node)
        elif isinstance(cst_node, cst.ClassDef):
            visit = self.enter_class_def(node, cst_node)
        elif isinstance(cst_node, cst.FunctionDef):
            visit = self.enter_function_def(node, cst_node)
        elif isinstance(cst_node, cst.AnnAssign):
            visit = self.enter_ann_assign(node, cst_node)
        elif isinstance(cst_node, cst.Assign):
            visit = self.enter_assign(node, cst_node)
        elif isinstance(cst_node, cst.SimpleStatementLine):
            visit = Visit.TraverseChildren
        elif isinstance(cst_node, cst.Expr):
            visit = Visit.SkipChildren
        elif isinstance(cst_node, (cst.Import, cst.ImportFrom)):
            visit = Visit.SkipChildren
        elif isinstance(cst_node, cst.Pass):
            visit = Visit.SkipChildren
        elif isinstance(cst_node, WHITESPACE):
            visit = Visit.TraverseChildren
        elif isinstance(cst_node, cst.Comment):
            visit = Visit.SkipChildren
        elif module_member and isinstance(cst_node, cst.CSTNode):
            logging.debug("skipping module member node %s", node)
            visit = Visit.SkipChildren
        else:
            raise Exception(f"unknown node type {node}")

        self.old_stack.append(_TransformContext(node=node))

        return visit

    def exit(self, node: Node) -> None:
        module_member = False

        self.old_stack.pop()
        if self.old_stack:
            self.old_stack[-1].child_offset += 1
            parent = self.old_stack[-1].node.cst_node
            module_member = isinstance(parent, cst.Module)

        assert isinstance(node, CstNode)
        cst_node = node.cst_node

        if isinstance(cst_node, cst.Module):
            self.exit_module(node)
        elif isinstance(cst_node, cst.ClassDef):
            self.exit_class_def()
        elif isinstance(cst_node, cst.FunctionDef):
            self.exit_function_def()
        elif isinstance(cst_node, cst.AnnAssign):
            self.exit_ann_assign()
        elif isinstance(cst_node, cst.Assign):
            self.exit_assign()
        elif isinstance(cst_node, cst.SimpleStatementLine):
            pass
        elif isinstance(cst_node, cst.Expr):
            pass
        elif isinstance(cst_node, (cst.ImportFrom, cst.Import)):
            pass
        elif isinstance(cst_node, cst.Pass):
            pass
        elif isinstance(cst_node, WHITESPACE):
            pass
        elif isinstance(cst_node, cst.Comment):
            pass
        elif module_member and isinstance(cst_node, cst.CSTNode):
            pass
        else:
            raise Exception(f"unknown node type {cst_node}")


class _AnnotationReferenceTransformVisitor(Visitor):
    root: Optional[Node]
    stack: Final[List[Node]]
    excluded_references: Final[FrozenSet[str]]

    def __init__(self, excluded_references: FrozenSet[str]) -> None:
        self.stack = []
        self.root = None
        self.excluded_references = excluded_references

    def enter(self, node: Node) -> Visit:
        if self.root is None:
            assert not self.stack
            self.root = node

        self.stack.append(node)

        if not isinstance(node, CstNode):
            return Visit.TraverseChildren

        cst_node = node.cst_node

        if isinstance(cst_node, cst.Attribute):
            # TODO: Need to figure out how to detect if a method is defined in
            #       a superclass (ex. `Foo.__name__`.)
            pass
        elif isinstance(cst_node, (cst.Name, cst.SimpleString)):
            if node.expression_context != ExpressionContext.STORE:
                self._make_reference(node)

        return Visit.TraverseChildren

    def _in_module(self, name: str, module: str) -> bool:
        module_parts = module.split(".")
        name_parts = name.split(".")

        try:
            return name_parts[: len(module_parts)] == module_parts
        except IndexError:
            return False

    def _make_reference(self, node: CstNode) -> None:
        for name in node.names:
            if name in self.excluded_references:
                continue

            if any(self._in_module(name, m) for m in node.all_modules):
                reference = Reference(
                    identifier=name,
                    child=node,
                )
                if len(self.stack) > 1:
                    self.stack[-2].replace_child(node, reference)
                else:
                    self.root = reference

    def exit(self, node: Node) -> None:
        self.stack.pop()


class _TypeVisitor(Visitor):
    root: Final[Node]
    type: Final[nodes.Type]

    def __init__(self, root: Node, type_: nodes.Type) -> None:
        self.root = root
        self.type = type_

    def enter(self, node: Node) -> Visit:
        if not isinstance(node, CstNode):
            return Visit.TraverseChildren

        cst_node = node.cst_node
        if isinstance(cst_node, cst.Name):
            self.type.child = self.root
        elif isinstance(cst_node, cst.SimpleString):
            self.type.child = self.root
        elif isinstance(cst_node, cst.Ellipsis):
            # TODO: check this.
            self.type.child = nodes.Name(name="...")
        elif isinstance(cst_node, cst.Attribute):
            if not node.names:
                raise NotImplementedError("attributes without full names")
            names = sorted(node.names)
            # TODO: While accurate, this doesn't match the exact text from the
            #       source file.
            self.type.child = nodes.Name(names[0], names[0])
        elif isinstance(cst_node, cst.Subscript):
            arguments = []
            generics = nodes.List(elements=ListNode(arguments))
            type_ = nodes.Type()

            self.type.child = nodes.Subscript(name=type_, generics=generics)

            value = node.find_child(cst_node.value)
            value.visit(_TypeVisitor(value, type_))

            for cst_element in cst_node.slice:
                # TODO: This traversal assumes no new nodes were added between
                #       the Subscript and the Index's contents.
                assert isinstance(cst_element, cst.SubscriptElement)
                element = node.find_child(cst_element)

                cst_index = cst_element.slice
                assert isinstance(cst_index, cst.Index)

                assert isinstance(element, CstNode)
                index = element.find_child(cst_index)
                generic = nodes.Type()

                cst_index_value = cst_index.value
                assert cst_index.star is None
                assert isinstance(index, CstNode)
                index_value = index.find_child(cst_index_value)

                index_value.visit(_TypeVisitor(index_value, generic))

                arguments.append(generic)
        elif isinstance(cst_node, (cst.List, cst.Tuple)):
            # For example: Callable[[<List>], None], Tuple[()]
            subscript = nodes.Subscript()
            self.type.child = subscript
            elements = []

            # TODO: This is a bit of a hack, since the argument list of a
            #       Callable isn't a type of its own.

            if isinstance(cst_node, cst.List):
                subscript.generics = nodes.List(elements=ListNode(elements))
            elif isinstance(cst_node, cst.Tuple):
                subscript.generics = nodes.Tuple(elements=ListNode(elements))
            else:
                raise NotImplementedError()

            for cst_element in cst_node.elements:
                # TODO: This traversal assumes no new nodes were added between
                #       the Subscript and the Index's contents.
                assert isinstance(cst_element, cst.Element)
                element = node.find_child(cst_element)

                cst_value = cst_element.value
                assert isinstance(element, CstNode)
                value = element.find_child(cst_value)

                type_ = nodes.Type()
                value.visit(_TypeVisitor(value, type_))
                elements.append(type_)
        elif isinstance(cst_node, cst.BinaryOperation):
            assert isinstance(node, CstNode)
            self._binary_operation(node, cst_node)
        else:
            raise Exception(str(node) + str(cst_node))

        return Visit.SkipChildren

    def exit(self, node: Node) -> None:
        pass

    def _binary_operation(
        self, node: CstNode, cst_node: cst.BinaryOperation
    ) -> None:
        if not isinstance(cst_node.operator, cst.BitOr):
            raise NotImplementedError(f"binary operation {cst_node.operator}")

        left_node = nodes.Type()
        right_node = nodes.Type()

        self.type.child = nodes.BinaryOperation(
            left=left_node, right=right_node, operator=nodes.BitOr()
        )

        left_child = node.find_child(cst_node.left)
        left_child.visit(_TypeVisitor(left_child, left_node))

        right_child = node.find_child(cst_node.right)
        right_child.visit(_TypeVisitor(right_child, right_node))


class _AnnotationTransformVisitor(Visitor):
    stack: Final[List[Node]]

    def __init__(self) -> None:
        self.stack = []

    def enter(self, node: Node) -> Visit:
        self.stack.append(node)

        if not isinstance(node, CstNode):
            return Visit.TraverseChildren

        cst_node = node.cst_node

        if not isinstance(cst_node, cst.Annotation):
            return Visit.TraverseChildren

        type_ = nodes.Type()

        self.stack[-2].replace_child(node, type_)
        self.stack[-1] = type_

        annotation = node.find_child(cst_node.annotation)

        annotation.visit(_TypeVisitor(annotation, type_))

        return Visit.SkipChildren

    def exit(self, node: Node) -> None:
        self.stack.pop()


class _NameTransformVisitor(Visitor):
    stack: Final[List[Node]]

    def __init__(self) -> None:
        self.stack = []

    def enter(self, node: Node) -> Visit:
        new_node = node
        if isinstance(node, CstNode):
            cst_node = node.cst_node
            if isinstance(cst_node, (cst.Name, cst.SimpleString)):
                names = sorted(node.names)
                try:
                    full_name = names[0]
                except IndexError:
                    full_name = None

                new_node = nodes.Name(cst_node.value, full_name)
            elif isinstance(cst_node, cst.Attribute):
                new_node = nodes.Access(
                    value=node.find_child(cst_node.value),
                    attribute=node.find_child(cst_node.attr),
                )

        if new_node != node:
            self.stack[-1].replace_child(node, new_node)

        self.stack.append(new_node)
        return Visit.TraverseChildren

    def exit(self, node: Node) -> None:
        self.stack.pop()


class _VerbatimTransform(Visitor):
    root: Optional[Node]
    stack: Final[List[Node]]

    @staticmethod
    def apply(source: TextSource, node: Node) -> Node:
        transform = _VerbatimTransform()

        node.visit(transform)

        verbatim = Verbatim(source)
        assert transform.root is not None
        verbatim.append(transform.root)
        return verbatim

    def __init__(self) -> None:
        self.stack = []
        self.root = None

    def enter(self, node: Node) -> Visit:
        if self.root is None:
            assert 0 == len(self.stack)
            self.root = node
        else:
            assert 0 < len(self.stack)

        self.stack.append(node)
        return Visit.TraverseChildren

    def exit(self, node: Node) -> None:
        popped = self.stack.pop()
        assert popped == node

        if not isinstance(node, CstNode):
            return

        if isinstance(node.cst_node, WHITESPACE):
            new = BlankNode()
        else:
            name = dasherize(underscore(node.cst_node.__class__.__name__))

            new = Fragment(
                start=node.start,
                end=node.end,
                highlights=[name],
            )

            for child in node.children:
                new.append(child)

        if self.stack:
            self.stack[-1].replace_child(node, new)
        else:
            assert self.root == node
            self.root = new
