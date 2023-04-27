"""
Create a block builder tool for the given fork.
"""

import argparse


def b11r_arguments(subparsers: argparse._SubParsersAction) -> None:
    """
    Adds the arguments for the b11r tool subparser.
    """
    b11r_parser = subparsers.add_parser("b11r", help="This is the b11r tool.")

    b11r_parser.add_argument(
        "--input.header", dest="input_header", type=str, default="header.json"
    )
    b11r_parser.add_argument("--input.ommers", dest="input_ommers", type=str)
    b11r_parser.add_argument(
        "--input.txs", dest="input_txs", type=str, default="txs.rlp"
    )
    b11r_parser.add_argument(
        "--input.withdrawals", dest="input_withdrawals", type=str
    )
    b11r_parser.add_argument(
        "--output.basedir", dest="output_basedir", type=str
    )
    b11r_parser.add_argument(
        "--output.block", dest="output_block", type=str, default="block.json"
    )
    b11r_parser.add_argument("--seal.clique", dest="seal_clique", type=str)
    b11r_parser.add_argument(
        "--seal.ethash",
        dest="seal_ethash",
        type=bool,
        default=False,
    )
    b11r_parser.add_argument(
        "--seal.ethash.dir", dest="seal_ethash_dir", type=str, default=None
    )
    b11r_parser.add_argument(
        "--seal.ethash.mode",
        dest="seal_ethash_mode",
        type=str,
        default="normal",
    )
    b11r_parser.add_argument(
        "--verbosity", dest="verbosity", type=int, default=3
    )


class B11R:
    """
    Creates the b11r tool.
    """

    def __init__(self, options: argparse.Namespace) -> None:
        """
        Initializes the b11r tool.
        """
        self.options = options

    def run(self) -> int:
        """
        Runs the b11r tool.
        """
        print("This is the b11r tool.")
        return 0
