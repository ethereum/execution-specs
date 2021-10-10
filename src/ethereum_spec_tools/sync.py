"""
Ethereum Sync
^^^^^^^^^^^^^

Using an RPC provider, fetch each block and validate it with the specification.
"""

import argparse
import json
import logging
import time
from queue import Empty, Full, Queue
from threading import Thread
from typing import Any, Dict, List, Optional, Union
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

    downloaded_blocks: Queue
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
        self.downloaded_blocks = Queue(maxsize=512)

    def module(self, name: str) -> Any:
        """
        Return a module from the current hard fork.
        """
        return self.active_fork.module(name)

    def fetch_blocks(
        self,
        first: int,
        count: int,
    ) -> List[Union[bytes, RpcError]]:
        """
        Fetch the block specified by the given number from the RPC provider as
        an RLP encoded byte array.
        """
        if count == 0:
            return []

        calls = []

        for number in range(first, first + count):
            calls.append(
                {
                    "jsonrpc": "2.0",
                    "id": hex(number),
                    "method": "debug_getBlockRlp",
                    "params": [number],
                }
            )

        data = json.dumps(calls).encode("utf-8")

        self.log.debug("fetching blocks [%s, %s)...", first, first + count)

        post = request.Request(
            self.options.rpc_url,
            data=data,
            headers={
                "Content-Length": str(len(data)),
                "Content-Type": "application/json",
            },
        )

        with request.urlopen(post) as response:
            replies = json.load(response)
            blocks: Dict[int, Union[RpcError, bytes]] = {}

            for reply in replies:
                reply_id = int(reply["id"], 0)

                if reply_id < first or reply_id >= first + count:
                    raise Exception("mismatched request id")

                if "error" in reply:
                    blocks[reply_id] = RpcError(
                        reply["error"]["code"],
                        reply["error"]["message"],
                    )
                else:
                    blocks[reply_id] = bytes.fromhex(reply["result"])

            if len(blocks) != count:
                raise Exception(
                    f"expected {count} blocks but only got {len(blocks)}"
                )

            self.log.info("blocks [%s, %s) fetched", first, first + count)

            return [v for (_, v) in sorted(blocks.items())]

    def download(self) -> None:
        """
        Fetch chunks of blocks from the RPC provider.
        """
        start = len(self.chain.blocks)
        running = True

        while running:
            count = max(1, self.downloaded_blocks.maxsize // 2)
            replies = self.fetch_blocks(start, count)

            for reply in replies:
                to_push: Optional[bytes]

                if isinstance(reply, RpcError):
                    if reply.code != -32000:
                        raise reply

                    logging.info("reached end of chain", exc_info=reply)
                    running = False
                    to_push = None
                else:
                    to_push = reply
                    start += 1

                # Use a loop+timeout so that KeyboardInterrupt is still raised.
                while True:
                    try:
                        self.downloaded_blocks.put(to_push, timeout=1)
                        break
                    except Full:
                        pass

    def take_block(self) -> Optional[bytes]:
        """
        Pop a block of the download queue.
        """
        # Use a loop+timeout so that KeyboardInterrupt is still raised.
        while True:
            try:
                return self.downloaded_blocks.get(timeout=1)
            except Empty:
                pass

    def process_blocks(self) -> None:
        """
        Validate blocks that have been fetched.
        """
        while True:
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

            encoded_block = self.take_block()

            if encoded_block is None:
                break

            block = self.module("rlp").decode_to_block(encoded_block)

            if block.header.number != block_number:
                raise Exception(
                    f"expected block {block_number} "
                    f"but got {block.header.number}"
                )

            self.log.debug("applying block %s...", block_number)

            start = time.monotonic()
            self.module("spec").state_transition(self.chain, block)
            end = time.monotonic()

            self.log.info(
                "block %s applied (took %ss)",
                block_number,
                end - start,
            )


def main() -> None:
    """
    Using an RPC provider, fetch each block and validate it.
    """
    logging.basicConfig(level=logging.INFO)

    sync = Sync()

    download = Thread(target=sync.download, name="download", daemon=True)
    download.start()

    sync.process_blocks()


if __name__ == "__main__":
    main()
