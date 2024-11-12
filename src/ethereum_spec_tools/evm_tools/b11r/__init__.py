"""
Create a block builder tool for the given fork.
"""

import argparse
import json
from typing import Optional, TextIO

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes32

from ethereum.crypto.hash import keccak256

from ..utils import get_stream_logger
from .b11r_types import Body, Header


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

    # TODO: POW seal is currently not supported by the specs.
    # This should be revisited
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

    def __init__(
        self, options: argparse.Namespace, out_file: TextIO, in_file: TextIO
    ) -> None:
        """
        Initializes the b11r tool.
        """
        self.options = options
        self.out_file = out_file
        self.in_file = in_file

        if "stdin" in (
            options.input_header,
            options.input_ommers,
            options.input_txs,
        ):
            stdin = json.load(in_file)
        else:
            stdin = None

        self.body: Body = Body(options, stdin)
        self.header: Header = Header(options, self.body, stdin)
        self.block_rlp: Optional[bytes] = None
        self.block_hash: Optional[Bytes32] = None

        self.logger = get_stream_logger("B11R")

    def build_block(self) -> None:
        """
        Builds the block.
        """
        self.logger.info("Building the block...")

        header_to_list = [
            value for value in vars(self.header).values() if value is not None
        ]

        block = [
            header_to_list,
            self.body.transactions,
            self.body.ommers,
        ]

        if self.body.withdrawals is not None:
            block.append(self.body.withdrawals)

        self.block_rlp = rlp.encode(block)
        self.block_hash = keccak256(rlp.encode(header_to_list))

    def run(self) -> int:
        """
        Runs the b11r tool.
        """
        self.build_block()

        if not self.block_rlp or not self.block_hash:
            raise ValueError(
                "Cannot output result. Block RLP or block hash is not built."
            )

        result = {
            "rlp": "0x" + self.block_rlp.hex(),
            "hash": "0x" + self.block_hash.hex(),
        }

        self.logger.info("Writing the result...")
        if self.options.output_block == "stdout":
            json.dump(result, self.out_file, indent=4)
        else:
            with open(self.options.output_block, "w") as f:
                json.dump(result, f, indent=4)
            self.logger.info(
                f"The result has been written to {self.options.output_block}."
            )

        return 0
