"""
Ethereum Sync
^^^^^^^^^^^^^

Using an RPC provider, fetch each block and validate it with the specification.
"""

import argparse
import base64
import json
import logging
import time
from queue import Empty, Full, Queue
from threading import Thread
from typing import Any, Dict, List, Optional, TypeVar, Union
from urllib import request

from ethereum import rlp
from ethereum.base_types import U256, Bytes0, Bytes256, Uint, Uint64
from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes8,
    hex_to_bytes32,
    hex_to_u256,
    hex_to_uint,
)

from .forks import Hardfork

EMPTY_TRIE_ROOT_STR = (
    "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
)
T = TypeVar("T")


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

        parser.add_argument(
            "--start",
            help="Start syncing from this block",
            type=int,
            default=None,
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

        self.forks = Hardfork.discover()
        self.active_fork_index = 0

        if self.options.optimized:
            import ethereum_optimized

            ethereum_optimized.monkey_patch(state_path=self.options.persist)
        else:
            if self.options.persist is not None:
                self.log.error("--perist is not supported without --optimized")
                exit(1)

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
            if self.options.start is None:
                self.chain = self.module("spec").BlockChain(
                    blocks=[],
                    state=state,
                    chain_id=None,
                )
                self.set_initial_fork(0)
                self.chain = self.module("spec").apply_fork(self.chain)
            else:
                self.set_initial_fork(self.options.start)
                self.chain = self.download_state(self.options.start, state)
        else:
            self.set_initial_fork(persisted_block)
            self.chain = self.module("spec").BlockChain(
                blocks=self.fetch_initial_blocks(persisted_block),
                state=state,
                chain_id=self.fetch_chain_id(state),
            )

    def set_initial_fork(self, block_number: int) -> None:
        """Set the initial fork, don't run any transitions."""
        self.active_fork_index = 0
        while self.next_fork and block_number >= self.next_fork.block:
            self.active_fork_index += 1
        self.log.info("initial fork is %s", self.active_fork.name)

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
            "fetching ommers [%s, %s]...",
            min(ommers_needed),
            max(ommers_needed),
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
                "ommers [%s, %s] fetched",
                min(ommers_needed),
                max(ommers_needed),
            )

            return {
                k: tuple(x for (_, x) in sorted(v.items()))
                for (k, v) in ommers.items()
            }

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

    def fetch_initial_blocks(self, block_number: int) -> List[Any]:
        """
        Fetch the blocks required to continue execution from `block_number`.
        """
        return self.fetch_blocks(
            max(0, block_number - 255), min(256, block_number + 1)
        )

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
            self.options.rpc_url,
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

    def download_state(self, block_number: int, state: Any) -> Any:
        """
        Fetch the state at `block_number`. Return a chain object.
        """
        next_token = ""
        with_storage = []
        while True:
            call = [
                {
                    "jsonrpc": "2.0",
                    "id": hex(1),
                    "method": "debug_accountRange",
                    "params": [
                        hex(block_number),
                        next_token,
                        256,
                        False,
                        True,
                        False,
                    ],
                }
            ]
            data = json.dumps(call).encode("utf-8")

            post = request.Request(
                self.options.rpc_url,
                data=data,
                headers={
                    "Content-Length": str(len(data)),
                    "Content-Type": "application/json",
                },
            )

            with request.urlopen(post) as response:
                reply = json.load(response)[0]
                assert reply["id"] == hex(1)
                for address, account in reply["result"]["accounts"].items():
                    if account["root"] != EMPTY_TRIE_ROOT_STR:
                        with_storage.append(address)
                    address = self.module("utils.hexadecimal").hex_to_address(
                        address
                    )
                    account = self.module("eth_types").Account(
                        nonce=Uint(account["nonce"]),
                        balance=U256(int(account["balance"])),
                        code=hex_to_bytes(account["code"])
                        if "code" in account
                        else bytes(),
                    )
                    self.module("state").set_account(state, address, account)

                if "next" in reply["result"]:
                    next_token = reply["result"]["next"]
                    self.log.info(
                        "downloading accounts (%.2f%%)",
                        int.from_bytes(base64.b64decode(next_token), "big")
                        / 2**256
                        * 100,
                    )
                else:
                    break

        chain = self.module("spec").BlockChain(
            blocks=self.fetch_initial_blocks(block_number),
            state=state,
            chain_id=self.download_chain_id(),
        )

        blockhash_str = "0x" + rlp.rlp_hash(chain.blocks[-1].header).hex()
        self.download_storage(blockhash_str, state, with_storage)

        assert (
            self.module("state").state_root(chain.state)
            == chain.blocks[-1].header.state_root
        )
        return chain

    def download_storage(
        self, blockhash_str: str, state: Any, with_storage: List[str]
    ) -> None:
        """
        Fetch all the storage keys in the accounts in `with_storage`.
        """
        count = 0
        next_tokens = []
        while with_storage != []:
            for _ in range(min(64, len(with_storage))):
                next_tokens.append([with_storage.pop(), ""])
            while next_tokens != []:
                calls = [
                    {
                        "jsonrpc": "2.0",
                        "id": hex(i),
                        "method": "debug_storageRangeAt",
                        "params": [
                            blockhash_str,
                            0,
                            address_str,
                            next_token,
                            256 // len(next_tokens),
                        ],
                    }
                    for i, (address_str, next_token) in enumerate(next_tokens)
                ]
                data = json.dumps(calls).encode("utf-8")

                post = request.Request(
                    self.options.rpc_url,
                    data=data,
                    headers={
                        "Content-Length": str(len(data)),
                        "Content-Type": "application/json",
                    },
                )

                with request.urlopen(post) as response:
                    for reply in json.load(response):
                        reply_id = int(reply["id"], base=16)
                        for slot in reply["result"]["storage"].values():
                            count += 1
                            self.module("state").set_storage(
                                state,
                                self.module(
                                    "utils.hexadecimal"
                                ).hex_to_address(next_tokens[reply_id][0]),
                                hex_to_bytes32(slot["key"]),
                                hex_to_u256(slot["value"]),
                            )

                        if reply["result"]["nextKey"] is not None:
                            next_tokens[reply_id][1] = reply["result"][
                                "nextKey"
                            ]
                        else:
                            next_tokens[reply_id] = ["", ""]
                next_tokens = [x for x in next_tokens if x != ["", ""]]
                self.log.info(
                    "downloading storage (%d remaining)",
                    len(with_storage) + len(next_tokens),
                )

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
                self.active_fork_index += 1
                self.log.debug("applying %s fork...", self.active_fork.name)
                start = time.monotonic()
                self.chain = self.module("spec").apply_fork(self.chain)
                end = time.monotonic()
                self.log.info(
                    "applied %s fork (took %ss)",
                    self.active_fork.name,
                    end - start,
                )

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

            if self.options.persist is not None:
                self.active_fork.optimized_module("state_db").set_metadata(
                    self.chain.state,
                    b"block_number",
                    str(block_number).encode(),
                )

            self.log.info(
                "block %s applied (took %ss)",
                block_number,
                end - start,
            )

            if block_number > 2220000 and block_number < 2463000:
                # Excessive DB load due to the Shanghai DOS attacks, requires
                # more regular DB commits
                if block_number % 100 == 0:
                    self.persist()
            if block_number > 2675000 and block_number < 2700598:
                # Excessive DB load due to state clearing, requires more
                # regular DB commits
                if block_number % 100 == 0:
                    self.persist()
            elif block_number % 1000 == 0:
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
