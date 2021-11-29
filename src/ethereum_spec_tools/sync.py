"""
Ethereum Sync
^^^^^^^^^^^^^

Using an RPC provider, fetch each block and validate it with the specification.
"""

import argparse
import copyreg
import dataclasses
import json
import logging
import os.path
import pickle
import time
from queue import Empty, Full, Queue
from threading import Thread
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from urllib import request

from ethereum import rlp
from ethereum.base_types import Bytes0, Bytes256
from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes8,
    hex_to_bytes32,
    hex_to_u256,
    hex_to_uint,
)

from .forks import Hardfork

T = TypeVar("T")


class DispatchTable:
    """
    `dict`-like object that maps types to their pickle implementation.

    Workaround for Python 3.7 not having `reducer_override`.
    """

    @staticmethod
    def construct_dataclass(t: Callable[..., T], d: Dict[str, Any]) -> T:
        """
        Create a new instance of `t`, expanding `d` as keyword arguments.
        """
        return t(**d)

    def reduce_dataclass(
        self, d: T
    ) -> Tuple[
        Callable[[Callable[..., T], Dict[str, Any]], T],
        Tuple[Type[T], Dict[str, Any]],
    ]:
        """
        Convert a dataclass into a tuple for pickling.
        """
        fields = dataclasses.fields(d)

        return (
            DispatchTable.construct_dataclass,
            (type(d), {f.name: getattr(d, f.name) for f in fields}),
        )

    def get(self, t: Type[T]) -> Callable[[T], Tuple]:
        """
        Return the value for key if key is in the dictionary, else `None`.
        """
        if dataclasses.is_dataclass(t):
            return self.reduce_dataclass
        else:
            return copyreg.dispatch_table.get(t)  # type: ignore

    def __getitem__(self, k: Type[T]) -> Callable[[T], Tuple]:
        """
        Return the value for key if key is in the dictionary.

        x.__getitem__(y) <==> x[y]
        """
        if dataclasses.is_dataclass(k):
            return self.reduce_dataclass
        else:
            return copyreg.dispatch_table[k]  # type: ignore


class DataclassPickler(pickle.Pickler):
    """
    A Pickler with special support for dataclasses.
    """

    dispatch_table = DispatchTable()  # type: ignore


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

        parser.add_argument(
            "--persist",
            help="save the block list and state periodically to this file",
        )

        parser.add_argument(
            "--geth",
            help="use geth specific RPC endpoints while fetching blocks",
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
        self.downloaded_blocks = Queue(maxsize=512)
        self.log = logging.getLogger(__name__)
        self.options = self.parse_arguments()

        database_path = None

        if self.options.persist is not None:
            database_path = os.path.join(self.options.persist, "state")

            try:
                os.mkdir(self.options.persist)
            except FileExistsError:
                pass

        if self.options.optimized:
            import ethereum_optimized

            ethereum_optimized.monkey_patch(state_path=database_path)

        self.forks = Hardfork.discover()
        self.active_fork_index = 0

        if self.options.persist is None:
            self.chain = self.module("spec").apply_fork(None)
            return

        self.log.debug("loading blocks and state...")

        blocks_path = os.path.join(self.options.persist, "blocks.pickle")

        blocks = []

        try:
            with open(blocks_path, "rb") as f:
                while True:
                    try:
                        blocks.extend(pickle.load(f))
                    except EOFError:
                        break
        except FileNotFoundError as e:
            self.log.warning("no block file found", exc_info=e)
            self.chain = self.module("spec").apply_fork(None)
            return

        if len(blocks) == 0:
            raise Exception("no blocks loaded")

        # TODO: Replace self.chain.state with the correct hard fork.

        if self.options.optimized:
            state = self.active_fork.optimized_module("state_db").State()
        else:
            state_path = os.path.join(self.options.persist, "state.pickle")

            try:
                with open(state_path, "rb") as f:
                    state = pickle.load(f)
            except FileNotFoundError as e:
                raise Exception("found blocks file but no state") from e

        self.chain = self.module("spec").BlockChain(
            blocks=blocks,
            state=state,
        )

        # TODO: Fast forward to correct hard fork.

        self.log.info("loaded state and %s blocks", len(self.chain.blocks))

    def persist(self) -> None:
        """
        Save the block list and state to file.
        """
        if self.options.persist is None:
            return

        self.log.debug("persisting blocks and state...")

        start = time.monotonic()

        temp_path = os.path.join(self.options.persist, "blocks.pickle.temp")
        blocks_path = os.path.join(self.options.persist, "blocks.pickle")

        with open(temp_path, "wb") as f:
            DataclassPickler(f).dump(self.chain.blocks)

        # If we are interrupted between `os.replace()` and
        # `commit_db_transaction()` the two files will get out of sync.
        os.replace(temp_path, blocks_path)

        if self.options.optimized:
            module = self.active_fork.optimized_module("state_db")
            module.commit_db_transaction(self.chain.state)
            module.begin_db_transaction(self.chain.state)
        else:
            state_path = os.path.join(self.options.persist, "state.pickle")

            with open(state_path, "wb") as f:
                DataclassPickler(f).dump(self.chain.state)

        end = time.monotonic()
        self.log.info(
            "persisted state and %s blocks (took %ss)",
            len(self.chain.blocks),
            end - start,
        )

    def module(self, name: str) -> Any:
        """
        Return a module from the current hard fork.
        """
        return self.active_fork.module(name)

    def make_header(self, json: Any) -> Any:
        """
        Create a Header object from JSON describing it.
        """
        return self.module("eth_types").Header(
            hex_to_bytes32(json["parentHash"]),
            hex_to_bytes32(json["sha3Uncles"]),
            self.module("utils.hexadecimal").hex_to_address(json["miner"]),
            hex_to_bytes32(json["stateRoot"]),
            hex_to_bytes32(json["transactionsRoot"]),
            hex_to_bytes32(json["receiptsRoot"]),
            Bytes256(hex_to_bytes(json["logsBloom"])),
            hex_to_uint(json["difficulty"]),
            hex_to_uint(json["number"]),
            hex_to_uint(json["gasLimit"]),
            hex_to_uint(json["gasUsed"]),
            hex_to_u256(json["timestamp"]),
            hex_to_bytes(json["extraData"]),
            hex_to_bytes32(json["mixHash"]),
            hex_to_bytes8(json["nonce"]),
        )

    def fetch_uncles(self, uncles_needed: Dict[int, int]) -> Dict[int, Any]:
        """
        Fetch the uncles for a given block from the RPC provider.
        """
        calls = []

        for (block_number, num_uncles) in uncles_needed.items():
            for i in range(num_uncles):
                calls.append(
                    {
                        "jsonrpc": "2.0",
                        "id": hex(block_number * 20 + i),
                        "method": "eth_getUncleByBlockNumberAndIndex",
                        "params": [hex(block_number), hex(i)],
                    }
                )

        if calls == []:
            return {}

        data = json.dumps(calls).encode("utf-8")

        self.log.debug(
            "fetching uncles [%s, %s]...",
            min(uncles_needed),
            max(uncles_needed),
        )

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
            uncles: Dict[int, Dict[int, Any]] = {}

            for reply in replies:
                reply_id = int(reply["id"], 0)

                if reply_id // 20 not in uncles:
                    uncles[reply_id // 20] = {}

                if "error" in reply:
                    raise RpcError(
                        reply["error"]["code"],
                        reply["error"]["message"],
                    )
                else:
                    uncles[reply_id // 20][reply_id % 20] = self.make_header(
                        reply["result"]
                    )

            self.log.info(
                "uncles [%s, %s] fetched",
                min(uncles_needed),
                max(uncles_needed),
            )

            return {
                k: tuple(x for (_, x) in sorted(v.items()))
                for (k, v) in uncles.items()
            }

    def fetch_blocks(
        self,
        first: int,
        count: int,
    ) -> List[Union[Any, RpcError]]:
        """
        Fetch the block specified by the given number from the RPC provider.
        """
        if self.options.geth:
            return self.fetch_blocks_debug(first, count)
        else:
            return self.fetch_blocks_eth(first, count)

    def fetch_blocks_debug(
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

    def fetch_blocks_eth(
        self,
        first: int,
        count: int,
    ) -> List[Union[Any, RpcError]]:
        """
        Fetch the block specified by the given number from the RPC provider
        using only standard endpoints.
        """
        if count == 0:
            return []

        calls = []

        for number in range(first, first + count):
            calls.append(
                {
                    "jsonrpc": "2.0",
                    "id": hex(number),
                    "method": "eth_getBlockByNumber",
                    "params": [hex(number), True],
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
            blocks: Dict[int, Union[RpcError, Any]] = {}
            headers: Dict[int, Any] = {}
            transaction_lists: Dict[int, List[Any]] = {}
            uncles_needed: Dict[int, int] = {}

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
                    res = reply["result"]
                    headers[reply_id] = self.make_header(res)
                    transactions = []
                    for t in res["transactions"]:
                        transactions.append(
                            self.module("eth_types").Transaction(
                                hex_to_u256(t["nonce"]),
                                hex_to_u256(t["gasPrice"]),
                                hex_to_u256(t["gas"]),
                                self.module(
                                    "utils.hexadecimal"
                                ).hex_to_address(t["to"])
                                if t["to"]
                                else Bytes0(b""),
                                hex_to_u256(t["value"]),
                                hex_to_bytes(t["input"]),
                                hex_to_u256(t["v"]),
                                hex_to_u256(t["r"]),
                                hex_to_u256(t["s"]),
                            )
                        )
                    transaction_lists[reply_id] = transactions
                    uncles_needed[reply_id] = len(res["uncles"])

            uncles = self.fetch_uncles(uncles_needed)
            for id in headers:
                blocks[id] = self.module("eth_types").Block(
                    headers[id],
                    tuple(transaction_lists[id]),
                    uncles.get(id, ()),
                )

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
        start = self.chain.blocks[-1].header.number + 1
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

    def take_block(self) -> Optional[Any]:
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
            block = self.take_block()

            if block is None:
                break

            try:
                block_number = self.chain.blocks[-1].header.number + 1
            except IndexError:
                block_number = 0

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

            if isinstance(block, bytes):
                # Decode the block using the rules for the active fork.
                block = rlp.decode_to(self.module("eth_types").Block, block)

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

            if block_number % 1000 == 0:
                self.persist()


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
