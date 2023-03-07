"""
Ethereum Test Filler
^^^^^^^^^^^^^^^^^^^^

Executes python test fillers to create "filled" tests (fixtures)
that can be consumed by ethereum execution clients.
"""
import argparse
import logging
from pathlib import Path

from .filler import Filler


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--evm-bin",
        help="path to evm executable that provides `t8n` and `b11r` \
              subcommands",
        default=None,
        type=Path,
    )

    parser.add_argument(
        "--filler-path",
        help="path to filler directives, default: ./fillers",
        default="fillers",
        type=Path,
    )

    parser.add_argument(
        "--output",
        help="directory to store filled test fixtures, \
              default: ./fixtures",
        default="fixtures",
        type=Path,
    )

    parser.add_argument(
        "--test-categories",
        type=str,
        nargs="+",
        help="limit to filling tests of specific categories",
    )

    parser.add_argument(
        "--test-module",
        help="limit to filling tests of a specific module",
    )

    parser.add_argument(
        "--test-case",
        help="limit to filling only tests with matching name",
    )

    parser.add_argument(
        "--traces",
        action="store_true",
        help="collect traces of the execution information from the \
              transition tool",
    )

    parser.add_argument(
        "--no-output-structure",
        action="store_true",
        help="removes the folder structure from test fixture output",
    )

    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="logs the timing of the test filler for benchmarking",
    )

    parser.add_argument(
        "--max-workers",
        type=int,
        help="specifies the max number of workers for the test filler \
              set to 1 for serial execution",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="fill all test fillers and don't skip any tests \
              overwriting where necessary",
    )

    return parser.parse_args()


def main() -> None:
    """
    Fills the specified test definitions.
    """
    logging.basicConfig(level=logging.DEBUG)

    filler = Filler(parse_arguments())
    filler.fill()
