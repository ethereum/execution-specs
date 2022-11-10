"""
Ethereum Test Filler
^^^^^^^^^^^^^^^^^^^^

Execute test fillers to create "filled" tests that can be consumed by execution
clients.
"""

import argparse
import importlib
import json
import logging
import os
import pkgutil
from pathlib import Path

import setuptools

from ethereum_test.types import JSONEncoder
from evm_block_builder import EvmBlockBuilder
from evm_transition_tool import EvmTransitionTool


class Filler:
    """
    A command line tool to process test fillers into full hydrated tests.
    """

    @staticmethod
    def parse_arguments() -> argparse.Namespace:
        """
        Parse command line arguments.
        """
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "--evm-bin",
            help="path to evm executable that provides `t8n` and `b11r` "
            + "subcommands",
            default=None,
            type=Path,
        )

        parser.add_argument(
            "--filler-path",
            help="path to filler directives",
        )

        parser.add_argument(
            "--output",
            help="directory to store filled test fixtures",
            default="out",
        )

        parser.add_argument(
            "--test-module",
            help="limit to filling tests of a specific module",
        )

        parser.add_argument(
            "--test-case",
            help="limit to filling only tests with matching name",
        )

        return parser.parse_args()

    options: argparse.Namespace
    log: logging.Logger

    def __init__(self) -> None:
        self.log = logging.getLogger(__name__)
        self.options = self.parse_arguments()

    def fill(self) -> None:
        """
        Fill test fixtures.
        """
        pkg_name = "ethereum_tests"
        pkg_path = os.path.join("src", "ethereum_tests")

        if self.options.filler_path is not None:
            pkg_name = os.path.basename(self.options.filler_path)
            pkg_path = self.options.filler_path

        fillers = []
        for module_name in find_modules(os.path.abspath(pkg_path)):
            if (
                self.options.test_module
                and self.options.test_module not in module_name
            ):
                continue
            self.log.debug(f"searching {module_name} for fillers")
            module = importlib.import_module(pkg_name + "." + module_name)
            for obj in module.__dict__.values():
                if callable(obj):
                    if hasattr(obj, "__filler_metadata__"):
                        if (
                            self.options.test_case
                            and self.options.test_case
                            not in obj.__filler_metadata__["name"]
                        ):
                            continue
                        obj.__filler_metadata__[
                            "module_path"
                        ] = module_name.split(".")
                        fillers.append(obj)

        self.log.info(f"collected {len(fillers)} fillers")

        os.makedirs(self.options.output, exist_ok=True)

        t8n = EvmTransitionTool(binary=self.options.evm_bin)
        b11r = EvmBlockBuilder(binary=self.options.evm_bin)

        for filler in fillers:
            name = filler.__filler_metadata__["name"]
            output_dir = os.path.join(
                self.options.output,
                *(filler.__filler_metadata__["module_path"]),
            )
            os.makedirs(output_dir, exist_ok=True)
            path = os.path.join(output_dir, f"{name}.json")

            self.log.debug(f"filling {name}")
            fixture = filler(t8n, b11r, "NoProof")

            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    fixture, f, ensure_ascii=False, indent=4, cls=JSONEncoder
                )


def find_modules(root):
    """
    Find modules recursively starting with the `root`.
    """
    modules = set()
    packages = [root] + setuptools.find_packages(root)
    for pkg in packages:
        for info in pkgutil.iter_modules([root + "/" + pkg]):
            if not info.ispkg:
                modules.add(pkg + "." + info.name)
    return modules


def main() -> None:
    """
    Fills the specified test definitions.
    """
    logging.basicConfig(level=logging.DEBUG)

    filler = Filler()
    filler.fill()
