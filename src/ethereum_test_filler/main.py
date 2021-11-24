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

import setuptools

from ethereum_test.types import JSONEncoder


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
            help="path to evm executable",
            default="evm",
        )

        parser.add_argument(
            "--filler-path",
            help="path to filler directives",
        )

        parser.add_argument(
            "--output", help="directory to store filled test fixtures"
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
        pkg_path = "src/ethereum_tests"

        if self.options.filler_path is not None:
            pkg_name = os.path.basename(self.options.filler_path)
            pkg_path = self.options.filler_path

        fillers = []
        for module in find_modules(os.path.abspath(pkg_path)):
            module = importlib.import_module(pkg_name + "." + module)
            for obj in module.__dict__.values():
                if callable(obj):
                    if hasattr(obj, "__filler_metadata__"):
                        fillers.append(obj)

        self.log.info(f"Collected {len(fillers)} fillers")

        try:
            os.mkdir(self.options.output)
        except FileExistsError:
            pass

        for filler in fillers:
            fixture = filler("NoProof")
            name = filler.__filler_metadata__["name"]
            fork = filler.__filler_metadata__["fork"].lower()
            path = os.path.join(self.options.output, f"{name}_{fork}.json")
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
    logging.basicConfig(level=logging.INFO)

    filler = Filler()
    filler.fill()
