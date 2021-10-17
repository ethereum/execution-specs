"""
Ethereum Test Filler
^^^^^^^^^^^^^^^^^^^^

Execute test fillers to create "filled" tests that can be consumed by execution
clients.
"""

import argparse

class Filler:
    """
    A command line tool to process test fillers into full hydrated tests.
    """

    @staticmethod
    def parse_arguments() -> argparse.Namespace:
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "--t8n-tool",
            help="path to evm t8n executable",
            default="evm",
        )

        parser.add_argument(
            "--filler-path",
            help="path to filler directives",
        )

        parser.add_argument(
            "--output",
            help="directory to store filled test fixtures"
        )

        return parser.parse_args()
