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
Command line interface to docc.
"""

import argparse
import logging
import sys
from contextlib import ExitStack
from io import TextIOBase
from pathlib import Path
from shutil import rmtree
from typing import Dict, Set, Type

from . import build, context, discover, transform
from .context import Context
from .document import Document, Node, OutputNode, Visit, Visitor
from .performance import measure
from .settings import Settings
from .source import Source


class _OutputVisitor(Visitor):
    destination: TextIOBase
    context: Context

    def __init__(self, context_: Context, destination: TextIOBase) -> None:
        self.context = context_
        self.destination = destination

    def enter(self, node: Node) -> Visit:
        if isinstance(node, OutputNode):
            node.output(self.context, self.destination)
            return Visit.SkipChildren
        else:
            return Visit.TraverseChildren

    def exit(self, node: Node) -> None:
        pass


def main() -> None:
    """
    Entry-point for the command line tool.
    """
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser(
        description="Python documentation generator."
    )

    parser.add_argument(
        "--output", help="The directory to write documentation to."
    )

    args = parser.parse_args()
    settings = Settings(Path.cwd())

    if args.output is None:
        output_root = settings.output.path

        if output_root is None:
            logging.critical(
                "Output path is required. "
                "Either define `tool.docc.output.path` in `pyproject.toml` "
                "or use `--output foo/bar` on the command line."
            )
            sys.exit(1)
    else:
        output_root = Path(args.output)

    with measure("Loaded plugins (%.4f s)", level=logging.INFO):
        discover_plugins = list(discover.load(settings))
        transform_plugins = list(transform.load(settings))
        context_plugins = list(context.load(settings))

    with measure("Created contexts (%.4f s)", level=logging.INFO):
        context_types = {}
        for name, context_plugin in context_plugins:
            class_ = context_plugin.provides()

            try:
                exists = context_types[class_]
                raise Exception(
                    f"context provider `{name}`"
                    f" conflicts with `{exists}`"
                    f" (on `{class_.__name__}`)"
                )
            except KeyError:
                pass

            context_types[class_] = name

    known: Set[Source] = set()

    with measure("Discovered sources (%.4f s)", level=logging.INFO):
        for name, instance in discover_plugins:
            found = instance.discover(frozenset(known))
            for item in found:
                if item.relative_path is None:
                    logging.debug("[%s] found source without a path", name)
                else:
                    logging.debug(
                        "[%s] found source: %s", name, item.relative_path
                    )
                known.add(item)

    with ExitStack() as exit_stack:
        build_plugins = [
            (n, exit_stack.enter_context(c)) for (n, c) in build.load(settings)
        ]

        with measure("Built documents (%.4f s)", level=logging.INFO):
            documents: Dict[Source, Document] = {}
            for name, build_plugin in build_plugins:
                before = len(documents)
                build_plugin.build(known, documents)
                after = len(documents)
                logging.debug("[%s] built %s documents", name, after - before)

        with measure("Provided contexts (%.4f s)", level=logging.INFO):
            contexts = {}
            for source, document in documents.items():
                context_dict: Dict[Type[object], object] = {
                    Document: document,
                    Source: source,
                }

                for _, context_plugin in context_plugins:
                    provided = context_plugin.provide()
                    class_ = context_plugin.provides()
                    assert class_ not in context_dict
                    context_dict[class_] = provided

                contexts[source] = Context(context_dict)

        with measure("Transformed documents (%.4f s)", level=logging.INFO):
            for _name, transform_plugin in transform_plugins:
                for context_ in contexts.values():
                    transform_plugin.transform(context_)

        rmtree(output_root, ignore_errors=True)

        with measure("Wrote outputs (%.4f s)", level=logging.INFO):
            for source, context_ in contexts.items():
                document = context_[Document]
                extension = document.extension()

                if extension is None:
                    logging.error(
                        "document from `%s` does not specify a file extension",
                        source.relative_path,
                    )
                    continue

                output_path = output_root / source.output_path
                output_path = Path(
                    output_path.with_suffix(output_path.suffix + extension)
                )

                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w", encoding="utf-8") as destination:
                    document.root.visit(_OutputVisitor(context_, destination))
