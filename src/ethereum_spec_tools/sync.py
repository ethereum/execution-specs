"""
Ethereum Sync
^^^^^^^^^^^^^

Using an RPC provider, fetch each block and validate it with the specification.
"""

import argparse
import json
import logging
import time
from typing import Any, List, Optional
from urllib import request

from .forks import Hardfork


class RpcError(Exception):
    """
    Error message and code returned by the RPC provider.
    """

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


class Sync:
    """
    A command line tool to fetch blocks from an RPC provider and validate them
    against the specification.
    """

    @staticmethod
    def parse_arguments() -> argparse.Namespace:
        """
        Parse command line arguments.
        """
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "--rpc-url",
            help="endpoint providing the Ethereum RPC API",
            default="http://localhost:8545/",
        )

        parser.add_argument(
            "--optimized",
            help="replace parts of the specification with optimized versions",
            action="store_true",
        )

        return parser.parse_args()

    forks: List[Hardfork]
    active_fork_index: int
    options: argparse.Namespace
    chain: Any
    log: logging.Logger

    @property
    def active_fork(self) -> Hardfork:
        """
        Currently executing hard fork.
        """
        return self.forks[self.active_fork_index]

    @property
    def next_fork(self) -> Optional[Hardfork]:
        """
        Hard fork that follows the currently executing hard fork.
        """
        try:
            return self.forks[self.active_fork_index + 1]
        except IndexError:
            return None

    def __init__(self) -> None:
        self.log = logging.getLogger(__name__)
        self.options = self.parse_arguments()

        if self.options.optimized:
            import ethereum_optimized

            ethereum_optimized.monkey_patch()

        self.forks = Hardfork.discover()
        self.active_fork_index = 0
        self.chain = self.module("spec").apply_fork(None)

    def module(self, name: str) -> Any:
        """
        Return a module from the current hard fork.
        """
        return self.active_fork.module(name)

    def fetch_block(self, number: int) -> bytes:
        """
        Fetch the block specified by the given number from the RPC provider as
        an RLP encoded byte array.
        """
        request_id = hex(number)

        call = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "debug_getBlockRlp",
            "params": [number],
        }

        data = json.dumps(call).encode("utf-8")

        self.log.debug("fetching block %s...", number)

        post = request.Request(
            self.options.rpc_url,
            data=data,
            headers={
                "Content-Length": str(len(data)),
                "Content-Type": "application/json",
            },
        )

        with request.urlopen(post) as response:
            reply = json.load(response)
            if reply["id"] != request_id:
                raise Exception("mismatched request id")

            if "error" in reply:
                raise RpcError(
                    reply["error"]["code"],
                    reply["error"]["message"],
                )

            self.log.info("block %s fetched", number)
            return bytes.fromhex(reply["result"])

    def process_block(self) -> None:
        """
        Fetch and validate the next block.
        """
        block_number = len(self.chain.blocks)

        if self.next_fork and block_number >= self.next_fork.block:
            self.log.debug("applying %s fork...", self.next_fork.name)
            start = time.monotonic()
            self.chain = self.module("spec").apply_fork(self.chain)
            end = time.monotonic()
            self.log.info(
                "applied %s fork (took %ss)",
                self.next_fork.name,
                end - start,
            )
            self.active_fork_index += 1

        encoded_block = self.fetch_block(block_number)
        block = self.module("rlp").decode_to_block(encoded_block)

        self.log.debug("applying block %s...", block_number)

        start = time.monotonic()
        self.module("spec").state_transition(self.chain, block)
        end = time.monotonic()

        self.log.info("block %s applied (took %ss)", block_number, end - start)


def main() -> None:
    """
    Using an RPC provider, fetch each block and validate it.
    """
    logging.basicConfig(level=logging.INFO)

    sync = Sync()

    try:
        while True:
            sync.process_block()
    except RpcError as e:
        if e.code == -32000:
            logging.info("reached end of chain", exc_info=e)
            return
        raise


if __name__ == "__main__":
    main()
