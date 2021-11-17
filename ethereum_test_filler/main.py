"""
Ethereum Test Filler
^^^^^^^^^^^^^^^^^^^^

Execute test fillers to create "filled" tests that can be consumed by execution
clients.
"""

import argparse
import importlib
import pkgutil

import setuptools

from ethereum_test.types import Fixture


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

    def __init__(self) -> None:
        self.options = self.parse_arguments()

    def fill(self) -> None:
        """
        Fill test fixtures.
        """
        print("Filling...")

        pkg_name = "ethereum_tests"

        import ethereum_tests

        def find_modules(path):
            modules = set()
            for pkg in setuptools.find_packages(path):
                modules.add(pkg)
                pkg_path = path + "/" + pkg.replace(".", "/")
                for info in pkgutil.iter_modules([pkg_path]):
                    if not info.ispkg:
                        modules.add(pkg + "." + info.name)
            return modules

        for module in find_modules(ethereum_tests.__path__[0]):
            module = importlib.import_module(pkg_name + "." + module)
            for obj in module.__dict__.values():
                if isinstance(obj, Fixture):
                    print(obj)


def main() -> None:
    """
    Fills the specified test definitions.
    """
    filler = Filler()
    filler.fill()
