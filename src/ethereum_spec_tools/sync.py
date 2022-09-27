"""
Ethereum Sync
^^^^^^^^^^^^^

Using an RPC provider, fetch each block and validate it with the specification.
"""

import argparse
import json
import logging
import os
import shutil
import time
from queue import Empty, Full, Queue
from threading import Thread
from typing import Any, Dict, List, Optional, TypeVar, Union
from urllib import request

from ethereum import genesis, rlp
from ethereum.base_types import Bytes0, Bytes256, Uint64
from ethereum.testnets import clique
from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes8,
    hex_to_bytes32,
    hex_to_u256,
    hex_to_uint,
)

from .forks import Hardfork

T = TypeVar("T")


class RpcError(Exception):
    """
    Error message and code returned by the RPC provider.
    """

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


class ForkTracking:
    """
    Enables subclasses to track the current fork.
    """

    forks: List[Hardfork]
    block_number: int
    active_fork_index: int

    def __init__(self, hardforks: List[Hardfork], block_number: int):
        self.forks = hardforks
        self.set_block(block_number)

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

    def module(self, name: str) -> Any:
        """
        Return a module from the current hard fork.
        """
        return self.active_fork.module(name)

    def set_block(self, block_number: int) -> None:
        """Set the block number and switch to the correct fork."""
        self.block_number = block_number
        self.active_fork_index = 0
        while self.next_fork and block_number >= self.next_fork.block:
            self.active_fork_index += 1

    def advance_block(self) -> bool:
        """Increment the block number, return `True` if the fork changed."""
        self.block_number += 1
        if self.next_fork and self.block_number >= self.next_fork.block:
            self.active_fork_index += 1
            return True
        return False


class BlockDownloader(ForkTracking):
    """Downloads blocks from the RPC provider."""

    queue: Queue
    log: logging.Logger
    rpc_url: str
    geth: bool

    def __init__(
        self,
        log: logging.Logger,
        rpc_url: str,
        geth: bool,
        hardforks: List[Hardfork],
        first_block: int,
    ) -> None:
        ForkTracking.__init__(self, hardforks, first_block)

        self.queue = Queue(maxsize=512)
        self.log = log
        self.rpc_url = rpc_url
        self.geth = geth

        Thread(target=self.download, name="download", daemon=True).start()

    def take_block(self) -> Optional[Any]:
        """
        Pop a block of the download queue.
        """
        # Use a loop+timeout so that KeyboardInterrupt is still raised.
        while True:
            try:
                return self.queue.get(timeout=1)
            except Empty:
                pass

    def download(self) -> None:
        """
        Fetch chunks of blocks from the RPC provider.
        """
        running = True

        while running:
            count = max(1, self.queue.maxsize // 2)
            if self.next_fork:
                # Don't fetch a batch across a fork boundary
                count = min(count, self.next_fork.block - self.block_number)
            replies = self.fetch_blocks(self.block_number, count)

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
                    self.advance_block()

                # Use a loop+timeout so that KeyboardInterrupt is still raised.
                while True:
                    try:
                        self.queue.put(to_push, timeout=1)
                        break
                    except Full:
                        pass

    def fetch_blocks(
        self,
        first: int,
        count: int,
    ) -> List[Union[Any, RpcError]]:
        """
        Fetch the block specified by the given number from the RPC provider.
        """
        if self.geth:
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

        self.log.debug("fetching blocks [%d, %d)...", first, first + count)

        post = request.Request(
            self.rpc_url,
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

            self.log.info("blocks [%d, %d) fetched", first, first + count)

            return [v for (_, v) in sorted(blocks.items())]

    def load_transaction(self, t: Any) -> Any:
        """
        Turn a json transaction into a `Transaction`.
        """
        if hasattr(self.module("eth_types"), "LegacyTransaction"):
            if t["type"] == "0x1":
                access_list = []
                for sublist in t.get("accessList", []):
                    access_list.append(
                        (
                            self.module("utils.hexadecimal").hex_to_address(
                                sublist.get("address")
                            ),
                            [
                                hex_to_bytes32(key)
                                for key in sublist.get("storageKeys")
                            ],
                        )
                    )
                return b"\x01" + rlp.encode(
                    self.module("eth_types").AccessListTransaction(
                        Uint64(1),
                        hex_to_u256(t["nonce"]),
                        hex_to_u256(t["gasPrice"]),
                        hex_to_u256(t["gas"]),
                        self.module("utils.hexadecimal").hex_to_address(
                            t["to"]
                        )
                        if t["to"]
                        else Bytes0(b""),
                        hex_to_u256(t["value"]),
                        hex_to_bytes(t["input"]),
                        access_list,
                        hex_to_u256(t["v"]),
                        hex_to_u256(t["r"]),
                        hex_to_u256(t["s"]),
                    )
                )
            else:
                return self.module("eth_types").LegacyTransaction(
                    hex_to_u256(t["nonce"]),
                    hex_to_u256(t["gasPrice"]),
                    hex_to_u256(t["gas"]),
                    self.module("utils.hexadecimal").hex_to_address(t["to"])
                    if t["to"]
                    else Bytes0(b""),
                    hex_to_u256(t["value"]),
                    hex_to_bytes(t["input"]),
                    hex_to_u256(t["v"]),
                    hex_to_u256(t["r"]),
                    hex_to_u256(t["s"]),
                )
        else:
            return self.module("eth_types").Transaction(
                hex_to_u256(t["nonce"]),
                hex_to_u256(t["gasPrice"]),
                hex_to_u256(t["gas"]),
                self.module("utils.hexadecimal").hex_to_address(t["to"])
                if t["to"]
                else Bytes0(b""),
                hex_to_u256(t["value"]),
                hex_to_bytes(t["input"]),
                hex_to_u256(t["v"]),
                hex_to_u256(t["r"]),
                hex_to_u256(t["s"]),
            )

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

        self.log.debug("fetching blocks [%d, %d)...", first, first + count)

        post = request.Request(
            self.rpc_url,
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
            ommers_needed: Dict[int, int] = {}

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
                        transactions.append(self.load_transaction(t))

                    transaction_lists[reply_id] = transactions
                    ommers_needed[reply_id] = len(res["uncles"])

            ommers = self.fetch_ommers(ommers_needed)
            for id in headers:
                blocks[id] = self.module("eth_types").Block(
                    headers[id],
                    tuple(transaction_lists[id]),
                    ommers.get(id, ()),
                )

            if len(blocks) != count:
                raise Exception(
                    f"expected {count} blocks but only got {len(blocks)}"
                )

            self.log.info("blocks [%d, %d) fetched", first, first + count)

            return [v for (_, v) in sorted(blocks.items())]

    def fetch_ommers(self, ommers_needed: Dict[int, int]) -> Dict[int, Any]:
        """
        Fetch the ommers for a given block from the RPC provider.
        """
        calls = []

        for (block_number, num_ommers) in ommers_needed.items():
            for i in range(num_ommers):
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
            "fetching ommers [%d, %d]...",
            min(ommers_needed),
            max(ommers_needed),
        )

        post = request.Request(
            self.rpc_url,
            data=data,
            headers={
                "Content-Length": str(len(data)),
                "Content-Type": "application/json",
            },
        )

        with request.urlopen(post) as response:
            replies = json.load(response)
            ommers: Dict[int, Dict[int, Any]] = {}

            for reply in replies:
                reply_id = int(reply["id"], 0)

                if reply_id // 20 not in ommers:
                    ommers[reply_id // 20] = {}

                if "error" in reply:
                    raise RpcError(
                        reply["error"]["code"],
                        reply["error"]["message"],
                    )
                else:
                    ommers[reply_id // 20][reply_id % 20] = self.make_header(
                        reply["result"]
                    )

            self.log.info(
                "ommers [%d, %d] fetched",
                min(ommers_needed),
                max(ommers_needed),
            )

            return {
                k: tuple(x for (_, x) in sorted(v.items()))
                for (k, v) in ommers.items()
            }

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

    def download_chain_id(self) -> Uint64:
        """
        Fetch the chain id of the executing chain from the rpc provider.
        """
        call = [
            {
                "jsonrpc": "2.0",
                "id": hex(2),
                "method": "eth_chainId",
                "params": [],
            }
        ]
        data = json.dumps(call).encode("utf-8")

        post = request.Request(
            self.rpc_url,
            data=data,
            headers={
                "Content-Length": str(len(data)),
                "Content-Type": "application/json",
            },
        )

        with request.urlopen(post) as response:
            reply = json.load(response)[0]
            assert reply["id"] == hex(2)
            chain_id = Uint64(int(reply["result"], 16))

        return chain_id


class Sync(ForkTracking):
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
            "--unoptimized",
            help="don't use the optimized state/ethash (extremely slow)",
            action="store_true",
        )

        parser.add_argument(
            "--persist",
            help="store the state in a db in this file",
        )

        parser.add_argument(
            "--geth",
            help="use geth specific RPC endpoints while fetching blocks",
            action="store_true",
        )

        parser.add_argument(
            "--reset",
            help="delete the db and start from scratch",
            action="store_true",
        )

        parser.add_argument(
            "--gas-per-commit",
            help="commit to db each time this much gas is consumed",
            type=int,
            default=1_000_000_000,
        )

        parser.add_argument(
            "--initial-state",
            help="start from the state in this db, rather than genesis",
        )

        parser.add_argument(
            "--stop-at", help="after syncing this block, exit successfully"
        )

        parser.add_argument(
            "--network",
            help="ethereum network to sync",
            choices=["mainnet", "goerli"],
            default="mainnet",
        )

        return parser.parse_args()

    downloader: BlockDownloader
    options: argparse.Namespace
    chain: Any
    log: logging.Logger

    def __init__(self) -> None:
        self.log = logging.getLogger(__name__)
        self.options = self.parse_arguments()

        if not self.options.unoptimized:
            import ethereum_optimized

            ethereum_optimized.monkey_patch(state_path=self.options.persist)
        else:
            if self.options.persist is not None:
                self.log.error("--persist is not supported with --unoptimized")
                exit(1)
            if self.options.initial_state is not None:
                self.log.error(
                    "--initial-state is not supported with --unoptimized"
                )
                exit(1)
            if self.options.reset:
                self.log.error("--reset is not supported with --unoptimized")
                exit(1)

        if self.options.persist is None:
            if self.options.initial_state is not None:
                self.log.error(
                    "--initial_state is not supported without --persist"
                )
                exit(1)
            if self.options.reset:
                self.log.error("--reset is not supported without --persist")
                exit(1)

        if self.options.network == "mainnet":
            # This import must happen after monkey patching
            import ethereum.hardforks

            self.hardforks = Hardfork.load(ethereum.hardforks.mainnet)
        elif self.options.network == "goerli":
            import ethereum.testnets.hardforks

            self.hardforks = Hardfork.load(ethereum.testnets.hardforks.goerli)

        ForkTracking.__init__(self, self.hardforks, 0)

        if self.options.reset:
            import rust_pyspec_glue

            rust_pyspec_glue.DB.delete(self.options.persist)

        if self.options.initial_state is not None:
            assert self.options.persist is not None
            if not os.path.exists(
                os.path.join(self.options.persist, "mdbx.dat")
            ):
                try:
                    os.mkdir(self.options.persist)
                except FileExistsError:
                    pass
                shutil.copy(
                    os.path.join(self.options.initial_state, "mdbx.dat"),
                    self.options.persist,
                )

        state = self.module("state").State()

        if self.options.persist is not None:
            persisted_block = self.active_fork.optimized_module(
                "state_db"
            ).get_metadata(state, b"block_number")

            if persisted_block is not None:
                persisted_block = int(persisted_block)
        else:
            persisted_block = None

        if persisted_block is None:
            self.downloader = BlockDownloader(
                self.log,
                self.options.rpc_url,
                self.options.geth,
                self.hardforks,
                1,
            )
            if self.options.network == "mainnet":
                chain_id = Uint64(1)
            elif self.options.network == "goerli":
                chain_id = Uint64(5)
            self.chain = self.module("spec").BlockChain(
                blocks=[],
                state=state,
                chain_id=chain_id,
            )
            if self.options.network == "mainnet":
                genesis_configuration = genesis.get_genesis_configuration(
                    "mainnet.json"
                )
            elif self.options.network == "goerli":
                genesis_configuration = genesis.get_genesis_configuration(
                    "goerli.json"
                )
            genesis.add_genesis_block(
                self.hardforks[0].mod,
                self.chain,
                genesis_configuration,
            )
            self.set_block(0)
        else:
            self.set_block(persisted_block)
            if persisted_block < 256:
                initial_blocks_length = persisted_block - 1
            else:
                initial_blocks_length = 255
            self.downloader = BlockDownloader(
                self.log,
                self.options.rpc_url,
                self.options.geth,
                self.hardforks,
                persisted_block - initial_blocks_length + 1,
            )
            blocks = []
            for _ in range(initial_blocks_length):
                blocks.append(self.downloader.take_block())
            self.chain = self.module("spec").BlockChain(
                blocks=blocks,
                state=state,
                chain_id=self.fetch_chain_id(state),
            )

    def persist(self) -> None:
        """
        Save the block list, state and chain id to file.
        """
        if self.options.persist is None:
            return

        self.log.debug("persisting blocks and state...")

        self.active_fork.optimized_module("state_db").set_metadata(
            self.chain.state,
            b"chain_id",
            str(self.chain.chain_id).encode(),
        )

        start = time.monotonic()

        module = self.active_fork.optimized_module("state_db")
        module.commit_db_transaction(self.chain.state)
        module.begin_db_transaction(self.chain.state)

        end = time.monotonic()
        self.log.info(
            "persisted state and %d blocks (took %.3f)",
            len(self.chain.blocks),
            end - start,
        )

    def fetch_chain_id(self, state: Any) -> Uint64:
        """
        Fetch the persisted chain id from the database.
        """
        chain_id = self.active_fork.optimized_module("state_db").get_metadata(
            state, b"chain_id"
        )

        if chain_id is not None:
            chain_id = Uint64(int(chain_id))

        return chain_id

    def process_blocks(self) -> None:
        """
        Validate blocks that have been fetched.
        """
        gas_since_last_commit = 0
        while True:
            if self.advance_block():
                self.log.debug("applying %s fork...", self.active_fork.name)
                start = time.monotonic()
                self.chain = self.module("spec").apply_fork(self.chain)
                end = time.monotonic()
                self.log.info(
                    "applied %s fork (took %.3f)",
                    self.active_fork.name,
                    end - start,
                )

            if self.chain.blocks:
                assert (
                    self.block_number
                    == self.chain.blocks[-1].header.number + 1
                )

            block = self.downloader.take_block()

            if block is None:
                break

            if isinstance(block, bytes):
                # Decode the block using the rules for the active fork.
                block = rlp.decode_to(self.module("eth_types").Block, block)

            if block.header.number != self.block_number:
                raise Exception(
                    f"expected block {self.block_number} "
                    f"but got {block.header.number}"
                )

            self.log.debug("applying block %d...", self.block_number)

            start = time.monotonic()
            if self.options.network == "mainnet":
                self.module("spec").state_transition(self.chain, block)
            elif self.options.network == "goerli":
                clique.state_transition(self.active_fork, self.chain, block)
            end = time.monotonic()

            # Additional gas to account for block overhead
            gas_since_last_commit += 30000
            gas_since_last_commit += block.header.gas_used

            if self.options.persist is not None:
                self.active_fork.optimized_module("state_db").set_metadata(
                    self.chain.state,
                    b"block_number",
                    str(self.block_number).encode(),
                )

            self.log.info(
                "block %d applied (took %.3fs)",
                self.block_number,
                end - start,
            )

            if self.block_number == self.options.stop_at:
                self.persist()
                return

            if self.block_number > 2220000 and self.block_number < 2463000:
                # Excessive DB load due to the Shanghai DOS attacks, requires
                # more regular DB commits
                if gas_since_last_commit > self.options.gas_per_commit / 10:
                    self.persist()
                    gas_since_last_commit = 0
            elif self.block_number > 2675000 and self.block_number < 2700598:
                # Excessive DB load due to state clearing, requires more
                # regular DB commits
                if gas_since_last_commit > self.options.gas_per_commit / 10:
                    self.persist()
                    gas_since_last_commit = 0
            elif gas_since_last_commit > self.options.gas_per_commit:
                self.persist()
                gas_since_last_commit = 0


def main() -> None:
    """
    Using an RPC provider, fetch each block and validate it.
    """
    logging.basicConfig(level=logging.INFO)

    sync = Sync()
    sync.process_blocks()


if __name__ == "__main__":
    main()
