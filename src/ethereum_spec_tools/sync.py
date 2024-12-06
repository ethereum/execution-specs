"""
Ethereum Sync
^^^^^^^^^^^^^

Using an RPC provider, fetch each block and validate it with the specification.
"""

import argparse
import json
import logging
import os
import pkgutil
import shutil
import time
from queue import Empty, Full, Queue
from threading import Thread
from typing import Any, Dict, List, Optional, TypeVar, Union, cast
from urllib import request

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes0, Bytes256
from ethereum_types.numeric import U64, U256, Uint

from ethereum import genesis
from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes8,
    hex_to_bytes32,
    hex_to_u64,
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
    block_number: Uint
    active_fork_index: int

    def __init__(
        self, forks: List[Hardfork], block_number: Uint, block_timestamp: U256
    ):
        self.forks = forks
        self.set_block(block_number, block_timestamp)

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

    def set_block(self, block_number: Uint, block_timestamp: U256) -> None:
        """Set the block number and switch to the correct fork."""
        self.block_number = block_number
        self.active_fork_index = 0
        while self.next_fork is not None and self.next_fork.has_activated(
            block_number, block_timestamp
        ):
            self.active_fork_index += 1

    def advance_block(self, timestamp: U256) -> bool:
        """Increment the block number, return `True` if the fork changed."""
        self.block_number += Uint(1)
        new_fork = False
        while self.next_fork is not None and self.next_fork.has_activated(
            self.block_number, timestamp
        ):
            self.active_fork_index += 1
            new_fork = True
        return new_fork


class BlockDownloader(ForkTracking):
    """Downloads blocks from the RPC provider."""

    queue: Queue
    log: logging.Logger
    rpc_url: str
    geth: bool

    def __init__(
        self,
        forks: List[Hardfork],
        log: logging.Logger,
        rpc_url: str,
        geth: bool,
        first_block: Uint,
        first_block_timestamp: U256,
    ) -> None:
        ForkTracking.__init__(self, forks, first_block, first_block_timestamp)

        # `first_block_timestamp` is the timestamp for the persisted block,
        #  but the downloader starts 256 blocks earlier. Since this might be
        #  the previous fork we step 1 fork backwards. In the case that there
        #  wasn't a fork in the previous 256 blocks, `advance_block()` will
        #  restore the correct fork before any blocks are processed.
        if self.active_fork_index > 0:
            self.active_fork_index -= 1

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
            count = Uint(max(1, self.queue.maxsize // 2))
            replies = self.fetch_blocks(self.block_number + Uint(1), count)

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

                # Use a loop+timeout so that KeyboardInterrupt is still raised.
                while True:
                    try:
                        self.queue.put(to_push, timeout=1)
                        break
                    except Full:
                        pass

    def fetch_blocks(
        self,
        first: Uint,
        count: Uint,
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
        first: Uint,
        count: Uint,
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
                    "method": "debug_getRawBlock",
                    "params": [hex(number)],
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
                "User-Agent": "ethereum-spec-sync",
            },
        )

        with request.urlopen(post) as response:
            replies = json.load(response)
            if not isinstance(replies, list):
                self.log.error(
                    "got non-list JSON-RPC response. replies=%r", replies
                )
                raise ValueError

            block_rlps: Dict[Uint, Union[RpcError, bytes]] = {}

            for reply in replies:
                try:
                    reply_id = Uint(int(reply["id"], 0))
                except Exception:
                    self.log.exception(
                        "unable to parse RPC id. reply=%r", reply
                    )
                    raise

                if reply_id < first or reply_id >= first + count:
                    raise Exception("mismatched request id")

                if "error" in reply:
                    block_rlps[reply_id] = RpcError(
                        reply["error"]["code"],
                        reply["error"]["message"],
                    )
                else:
                    block_rlps[reply_id] = bytes.fromhex(reply["result"][2:])

            if len(block_rlps) != count:
                raise Exception(
                    f"expected {count} blocks but only got {len(block_rlps)}"
                )

            self.log.info("blocks [%d, %d) fetched", first, first + count)

            blocks: List[Union[RpcError, Any]] = []
            for _, block_rlp in sorted(block_rlps.items()):
                if isinstance(block_rlp, RpcError):
                    blocks.append(block_rlp)
                else:
                    # Unfortunately we have to decode the RLP twice.
                    decoded_block = rlp.decode(block_rlp)
                    assert not isinstance(decoded_block, bytes)
                    assert not isinstance(decoded_block[0], bytes)
                    assert isinstance(decoded_block[0][11], bytes)
                    timestamp = U256.from_be_bytes(decoded_block[0][11])
                    self.advance_block(timestamp)
                    try:
                        blocks.append(
                            rlp.decode_to(
                                self.module("blocks").Block, block_rlp
                            )
                        )
                    except Exception:
                        self.log.exception(
                            "failed to decode block %d with timestamp %d",
                            self.block_number,
                            timestamp,
                        )
                        raise

            return blocks

    def load_transaction(self, t: Any) -> Any:
        """
        Turn a json transaction into a `Transaction`.
        """
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
        if hasattr(self.module("transactions"), "LegacyTransaction"):
            if t["type"] == "0x1":
                return b"\x01" + rlp.encode(
                    self.module("transactions").AccessListTransaction(
                        hex_to_u64(t["chainId"]),
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
            elif t["type"] == "0x2":
                return b"\x02" + rlp.encode(
                    self.module("transactions").FeeMarketTransaction(
                        hex_to_u64(t["chainId"]),
                        hex_to_u256(t["nonce"]),
                        hex_to_u256(t["maxPriorityFeePerGas"]),
                        hex_to_u256(t["maxFeePerGas"]),
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
                return self.module("transactions").LegacyTransaction(
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
            return self.module("transactions").Transaction(
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
        first: Uint,
        count: Uint,
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
                "User-Agent": "ethereum-spec-sync",
            },
        )

        with request.urlopen(post) as response:
            replies = json.load(response)
            block_jsons: Dict[Uint, Any] = {}
            ommers_needed: Dict[Uint, int] = {}
            blocks: Dict[Uint, Union[Any, RpcError]] = {}

            for reply in replies:
                reply_id = Uint(int(reply["id"], 0))

                if reply_id < first or reply_id >= first + count:
                    raise Exception("mismatched request id")

                if "error" in reply:
                    blocks[reply_id] = RpcError(
                        reply["error"]["code"],
                        reply["error"]["message"],
                    )
                else:
                    res = reply["result"]
                    if res is None:
                        from time import sleep

                        sleep(12)
                        break

                    block_jsons[reply_id] = res
                    ommers_needed[reply_id] = len(res["uncles"])

            ommers = self.fetch_ommers(ommers_needed)
            for id in block_jsons:
                self.advance_block(hex_to_u256(block_jsons[id]["timestamp"]))
                blocks[id] = self.make_block(
                    block_jsons[id], ommers.get(id, ())
                )

            self.log.info("blocks [%d, %d) fetched", first, first + count)

            return [v for (_, v) in sorted(blocks.items())]

    def fetch_ommers(self, ommers_needed: Dict[Uint, int]) -> Dict[Uint, Any]:
        """
        Fetch the ommers for a given block from the RPC provider.
        """
        calls = []

        for block_number, num_ommers in ommers_needed.items():
            for i in range(num_ommers):
                calls.append(
                    {
                        "jsonrpc": "2.0",
                        "id": hex(block_number * Uint(20) + Uint(i)),
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
                "User-Agent": "ethereum-spec-sync",
            },
        )

        with request.urlopen(post) as response:
            replies = json.load(response)
            ommers: Dict[Uint, Dict[Uint, Any]] = {}

            twenty = Uint(20)
            for reply in replies:
                reply_id = Uint(int(reply["id"], 0))

                if reply_id // twenty not in ommers:
                    ommers[reply_id // twenty] = {}

                if "error" in reply:
                    raise RpcError(
                        reply["error"]["code"],
                        reply["error"]["message"],
                    )
                else:
                    ommers[reply_id // twenty][
                        reply_id % twenty
                    ] = self.make_header(reply["result"])

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
        fields = [
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
        ]
        if hasattr(self.module("blocks").Header, "base_fee_per_gas"):
            fields.append(hex_to_uint(json["baseFeePerGas"]))
        if hasattr(self.module("blocks").Header, "withdrawals_root"):
            fields.append(hex_to_bytes32(json["withdrawalsRoot"]))
        return self.module("blocks").Header(*fields)

    def make_block(self, json: Any, ommers: Any) -> Any:
        """
        Create a block from JSON describing it.
        """
        header = self.make_header(json)
        transactions = []
        for t in json["transactions"]:
            transactions.append(self.load_transaction(t))

        if json.get("withdrawals") is not None:
            withdrawals = []
            for j in json["withdrawals"]:
                withdrawals.append(
                    self.module("blocks").Withdrawal(
                        hex_to_u64(j["index"]),
                        hex_to_u64(j["validatorIndex"]),
                        self.module("utils.hexadecimal").hex_to_address(
                            j["address"]
                        ),
                        hex_to_u256(j["amount"]),
                    )
                )

        extra_fields = []
        if hasattr(self.module("blocks").Block, "withdrawals"):
            extra_fields.append(withdrawals)

        return self.module("blocks").Block(
            header,
            tuple(transactions),
            ommers,
            *extra_fields,
        )

    def download_chain_id(self) -> U64:
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
                "User-Agent": "ethereum-spec-sync",
            },
        )

        with request.urlopen(post) as response:
            reply = json.load(response)[0]
            assert reply["id"] == hex(2)
            chain_id = U64(int(reply["result"], 16))

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
            "--stop-at",
            help="after syncing this block, exit successfully",
            type=int,
        )

        parser.add_argument(
            "--mainnet",
            help="Set the chain to mainnet",
            action="store_const",
            dest="chain",
            const="mainnet",
            default="mainnet",
        )
        parser.add_argument(
            "--zhejiang",
            help="Set the chain to mainnet",
            action="store_const",
            dest="chain",
            const="zhejiang",
        )
        parser.add_argument(
            "--sepolia",
            help="Set the chain to mainnet",
            action="store_const",
            dest="chain",
            const="sepolia",
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

        config_str = cast(
            bytes,
            pkgutil.get_data("ethereum", f"assets/{self.options.chain}.json"),
        ).decode()
        config = json.loads(config_str)

        if self.options.chain == "mainnet":
            forks = Hardfork.discover()
        else:
            forks = Hardfork.load_from_json(config)

        ForkTracking.__init__(self, forks, Uint(0), U256(0))

        if self.options.reset:
            import rust_pyspec_glue

            assert self.options.persist is not None
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

        persisted_block: Optional[Uint] = None
        persisted_block_timestamp: Optional[U256] = None

        if self.options.persist is not None:
            state_mod = self.module("state")
            persisted_block_opt = state_mod.get_metadata(
                state, b"block_number"
            )
            persisted_block_timestamp_opt = state_mod.get_metadata(
                state, b"block_timestamp"
            )

            if persisted_block_opt is not None:
                persisted_block = Uint(int(persisted_block_opt))
            if persisted_block_timestamp_opt is not None:
                persisted_block_timestamp = U256(
                    int(persisted_block_timestamp_opt)
                )

        if persisted_block is None or persisted_block_timestamp is None:
            self.chain = self.module("fork").BlockChain(
                blocks=[],
                state=state,
                chain_id=None,
            )
            genesis_configuration = genesis.get_genesis_configuration(
                f"{self.options.chain}.json"
            )

            description: genesis.GenesisFork = genesis.GenesisFork(
                Address=self.active_fork.module("fork_types").Address,
                Account=self.active_fork.module("fork_types").Account,
                Trie=self.active_fork.module("trie").Trie,
                Bloom=self.active_fork.module("fork_types").Bloom,
                Header=self.active_fork.module("blocks").Header,
                Block=self.active_fork.module("blocks").Block,
                set_account=self.active_fork.module("state").set_account,
                set_storage=self.active_fork.module("state").set_storage,
                state_root=self.active_fork.module("state").state_root,
                root=self.active_fork.module("trie").root,
                hex_to_address=self.active_fork.module(
                    "utils.hexadecimal"
                ).hex_to_address,
            )
            genesis.add_genesis_block(
                description,
                self.chain,
                genesis_configuration,
            )
            self.downloader = BlockDownloader(
                forks,
                self.log,
                self.options.rpc_url,
                self.options.geth,
                Uint(0),
                genesis_configuration.timestamp,
            )
            self.set_block(Uint(0), genesis_configuration.timestamp)
        else:
            self.set_block(persisted_block, persisted_block_timestamp)
            if persisted_block < Uint(256):
                initial_blocks_length = persisted_block
            else:
                initial_blocks_length = Uint(255)
            self.downloader = BlockDownloader(
                forks,
                self.log,
                self.options.rpc_url,
                self.options.geth,
                persisted_block - initial_blocks_length,
                persisted_block_timestamp,
            )
            blocks = []
            for _ in range(initial_blocks_length):
                blocks.append(self.downloader.take_block())
            self.chain = self.module("fork").BlockChain(
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

        state_mod = self.module("state")
        state_mod.set_metadata(
            self.chain.state,
            b"chain_id",
            str(self.chain.chain_id).encode(),
        )

        start = time.monotonic()

        state_mod.commit_db_transaction(self.chain.state)
        state_mod.begin_db_transaction(self.chain.state)

        end = time.monotonic()
        self.log.info(
            "persisted state and %d blocks (took %.3f)",
            len(self.chain.blocks),
            end - start,
        )

    def fetch_chain_id(self, state: Any) -> U64:
        """
        Fetch the persisted chain id from the database.
        """
        state_mod = self.module("state")
        chain_id = state_mod.get_metadata(state, b"chain_id")

        if chain_id is not None:
            chain_id = U64(int(chain_id))

        return chain_id

    def process_blocks(self) -> None:
        """
        Validate blocks that have been fetched.
        """
        time_of_last_commit = time.monotonic()
        gas_since_last_commit = 0
        last_committed_block: Optional[int] = None
        block: Optional[Any] = None

        def persist() -> None:
            nonlocal time_of_last_commit
            nonlocal gas_since_last_commit
            nonlocal last_committed_block

            now = time.monotonic()
            elapsed = now - time_of_last_commit
            time_of_last_commit = now

            if elapsed == 0:
                elapsed = 1

            m_gas = gas_since_last_commit / 1_000_000.0
            m_gas_per_second = m_gas / elapsed
            gas_since_last_commit = 0

            if block is not None:
                count = block.header.number
                if last_committed_block is not None:
                    count -= last_committed_block
                last_committed_block = block.header.number

                self.log.info(
                    "imported chain segment "
                    "count=%d mgas=%f mgasps=%f block=%d",
                    count,
                    m_gas,
                    m_gas_per_second,
                    block.header.number,
                )

            self.persist()

        while True:
            block = self.downloader.take_block()

            if block is None:
                break

            try:
                self.process_block(block)
            except Exception:
                self.log.exception(
                    "failed to process block %d", block.header.number
                )
                raise

            # Additional gas to account for block overhead
            gas_since_last_commit += 30000
            gas_since_last_commit += int(block.header.gas_used)

            if self.options.persist is not None:
                state_mod = self.module("state")
                state_mod.set_metadata(
                    self.chain.state,
                    b"block_number",
                    str(self.block_number).encode(),
                )
                state_mod.set_metadata(
                    self.chain.state,
                    b"block_timestamp",
                    str(block.header.timestamp).encode(),
                )

            self.log.debug(
                "block %d applied",
                self.block_number,
            )

            if self.block_number == self.options.stop_at:
                persist()
                return

            if self.block_number > Uint(2220000) and self.block_number < Uint(
                2463000
            ):
                # Excessive DB load due to the Shanghai DOS attacks, requires
                # more regular DB commits
                if gas_since_last_commit > self.options.gas_per_commit / 10:
                    persist()
            elif self.block_number > Uint(
                2675000
            ) and self.block_number < Uint(2700598):
                # Excessive DB load due to state clearing, requires more
                # regular DB commits
                if gas_since_last_commit > self.options.gas_per_commit / 10:
                    persist()
            elif gas_since_last_commit > self.options.gas_per_commit:
                persist()

    def process_block(self, block: Any) -> None:
        """
        Process a single block.
        """
        if (
            self.advance_block(block.header.timestamp)
            or self.block_number == 1
        ):
            self.log.debug("applying %s fork...", self.active_fork.name)
            start = time.monotonic()
            self.chain = self.module("fork").apply_fork(self.chain)
            end = time.monotonic()
            self.log.info(
                "applied %s fork (took %.3f)",
                self.active_fork.name,
                end - start,
            )

        assert (not self.chain.blocks) or (
            self.block_number == self.chain.blocks[-1].header.number + Uint(1)
        )

        if block.header.number != self.block_number:
            raise Exception(
                f"expected block {self.block_number} "
                f"but got {block.header.number}"
            )

        self.log.debug("applying block %d...", self.block_number)

        self.module("fork").state_transition(self.chain, block)


def main() -> None:
    """
    Using an RPC provider, fetch each block and validate it.
    """
    logging.basicConfig(level=logging.INFO)

    sync = Sync()
    sync.process_blocks()


if __name__ == "__main__":
    main()
