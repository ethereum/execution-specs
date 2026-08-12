"""
Load a hive client genesis file into an Amsterdam blockchain.

Hive simulators hand clients a genesis file containing the fixture's
genesis block header fields together with an `alloc` object describing
the pre-state. This module parses that file into a [`BlockChain`] ready
to accept payloads through the execution engine interface.

[`BlockChain`]: ref:ethereum.forks.amsterdam.fork.BlockChain
"""

import json
from pathlib import Path
from typing import Any, Mapping

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.forks.amsterdam.blocks import Block, Header
from ethereum.forks.amsterdam.fork import BlockChain
from ethereum.forks.amsterdam.fork_types import Bloom
from ethereum.state import Account, Address, Root
from ethereum.state_mpt import (
    State,
    set_account,
    set_storage,
    state_root,
    store_code,
)


def _bytes(value: Any) -> bytes:
    """Convert a `0x`-prefixed hex string to bytes."""
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ValueError(f"expected hex string, got {value!r}")
    return bytes.fromhex(value[2:])


def _int(value: Any) -> int:
    """Convert a hex string or plain integer to an integer."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 16)
    raise ValueError(f"expected integer or hex string, got {value!r}")


def genesis_header_from_json(genesis: Mapping[str, Any]) -> Header:
    """
    Build the genesis block header from a hive genesis file.

    The field names follow the blockchain test fixture header encoding,
    which is what the consume simulators write for the client.
    """
    return Header(
        parent_hash=Hash32(_bytes(genesis["parentHash"])),
        ommers_hash=Hash32(_bytes(genesis["uncleHash"])),
        coinbase=Address(_bytes(genesis["coinbase"])),
        state_root=Root(_bytes(genesis["stateRoot"])),
        transactions_root=Root(_bytes(genesis["transactionsTrie"])),
        receipt_root=Root(_bytes(genesis["receiptTrie"])),
        bloom=Bloom(_bytes(genesis["bloom"])),
        difficulty=Uint(_int(genesis["difficulty"])),
        number=Uint(_int(genesis["number"])),
        gas_limit=Uint(_int(genesis["gasLimit"])),
        gas_used=Uint(_int(genesis["gasUsed"])),
        timestamp=U256(_int(genesis["timestamp"])),
        extra_data=Bytes(_bytes(genesis["extraData"])),
        prev_randao=Bytes32(_bytes(genesis["mixHash"])),
        nonce=Bytes8(_bytes(genesis["nonce"])),
        base_fee_per_gas=Uint(_int(genesis["baseFeePerGas"])),
        withdrawals_root=Root(_bytes(genesis["withdrawalsRoot"])),
        blob_gas_used=U64(_int(genesis["blobGasUsed"])),
        excess_blob_gas=U64(_int(genesis["excessBlobGas"])),
        parent_beacon_block_root=Root(
            _bytes(genesis["parentBeaconBlockRoot"])
        ),
        requests_hash=Hash32(_bytes(genesis["requestsHash"])),
        block_access_list_hash=Hash32(_bytes(genesis["blockAccessListHash"])),
        slot_number=U64(_int(genesis["slotNumber"])),
    )


def state_from_alloc(alloc: Mapping[str, Any]) -> State:
    """
    Build the genesis state from a hive genesis `alloc` object.

    Account keys may appear with or without a `0x` prefix.
    """
    state = State()
    for address_hex, account in alloc.items():
        address = Address(bytes.fromhex(address_hex.removeprefix("0x")))
        code_hash = store_code(state, Bytes(_bytes(account.get("code", "0x"))))
        set_account(
            state,
            address,
            Account(
                nonce=Uint(_int(account.get("nonce", 0))),
                balance=U256(_int(account.get("balance", 0))),
                code_hash=code_hash,
            ),
        )
        for key, value in account.get("storage", {}).items():
            set_storage(
                state,
                address,
                Bytes32(_int(key).to_bytes(32, "big")),
                U256(_int(value)),
            )
    return state


def load_genesis_chain(genesis_path: Path, chain_id: U64) -> BlockChain:
    """
    Load a hive genesis file into a single-block chain.

    The state built from `alloc` must produce the header's `state_root`,
    and when the file carries the expected genesis `hash`, the header
    must reproduce it.
    """
    genesis = json.loads(genesis_path.read_text())

    header = genesis_header_from_json(genesis)
    state = state_from_alloc(genesis.get("alloc", {}))

    computed_state_root = state_root(state)
    if computed_state_root != header.state_root:
        raise ValueError(
            f"alloc state root {computed_state_root.hex()} does not match "
            f"genesis header state root {header.state_root.hex()}"
        )

    block_hash = keccak256(rlp.encode(header))
    if "hash" in genesis and block_hash != Hash32(_bytes(genesis["hash"])):
        raise ValueError(
            f"computed genesis hash {block_hash.hex()} does not match "
            f"declared genesis hash {genesis['hash']}"
        )

    return BlockChain(
        blocks=[
            Block(header=header, transactions=(), ommers=(), withdrawals=())
        ],
        state=state,
        chain_id=chain_id,
    )
