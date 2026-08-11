"""
One chain, described once and rendered for both sides.

The comparison is only meaningful if go-ethereum and the specification
start from the same state, and the cheapest way to be sure of that is to
derive both from a single allocation. [`genesis_json`] renders the form
`geth init` wants; [`genesis_state`] renders the [`State`] the spec
executes against; and [`GENESIS_HEADER`] is built by the spec's own
`Header` class so that the harness can check its idea of the genesis
block hash against the client's before it trusts anything downstream.

[`State`]: ref:ethereum.state_mpt.State
"""

from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes20
from ethereum_types.numeric import U64, U256, Uint
from execution_testing import Op

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.merkle_patricia_trie import EMPTY_TRIE_ROOT
from ethereum.state import EMPTY_CODE_HASH, Account
from ethereum.state_mpt import State, set_account, state_root, store_code
from ethereum_spec_tools.evm_tools.simulate import BaseBlock
from ethereum_spec_tools.evm_tools.simulate.context import (
    EMPTY_OMMERS_HASH,
    SimulateFork,
    resolve_simulate_fork,
)

FORK_NAME = "cancun"
"""
The fork the comparison runs at.

Cancun rather than Amsterdam, because go-ethereum has to be able to
answer too, and a development fork it does not implement would leave
nothing to compare against. The tool itself is fork-generic; only this
harness is pinned.
"""

CHAIN_ID = U64(1)
GAS_LIMIT = Uint(0x2FEFD8)
BASE_FEE_PER_GAS = Uint(7)


class Allocation(NamedTuple):
    """One account in the genesis allocation."""

    address: str
    balance: int
    code: Bytes = Bytes(b"")


def _address(value: str) -> Bytes20:
    """Parse a hex address."""
    return Bytes20(bytes.fromhex(value.removeprefix("0x")))


SENDER = "0xc000000000000000000000000000000000000000"
RECIPIENT = "0xc100000000000000000000000000000000000000"
THIRD_PARTY = "0xc200000000000000000000000000000000000000"
PAUPER = "0xc300000000000000000000000000000000000000"
"""A funded-with-nothing sender, for the insufficient-funds case."""

EMPTY_ACCOUNT_ADDRESS = "0xc400000000000000000000000000000000000000"
"""
An account that exists with nothing in it.

EIP-161 makes such an account impossible to create on mainnet, so
nothing on chain reaches it — but a state override conjures one on
demand, which is how a corner no consensus test covers becomes newly
reachable.
"""

LOGGER = "0xd000000000000000000000000000000000000000"
REVERTER = "0xd100000000000000000000000000000000000000"
CONTEXT_READER = "0xd200000000000000000000000000000000000000"
FORWARDER = "0xd300000000000000000000000000000000000000"
SELF_DESTRUCTOR = "0xd400000000000000000000000000000000000000"
BLOCKHASH_READER = "0xd500000000000000000000000000000000000000"
GAS_BURNER = "0xd600000000000000000000000000000000000000"

LOGGER_CODE = Bytes(bytes(Op.LOG0(0, 0) + Op.STOP))
"""Emit one empty log, so a call has something to report."""

REVERTER_CODE = Bytes(
    bytes(Op.MSTORE(0, 0xDEAD) + Op.REVERT(0, 32)),
)
"""Revert with a word, so the revert data has somewhere to show up."""

CONTEXT_READER_CODE = Bytes(
    bytes(
        Op.SSTORE(0, Op.NUMBER)
        + Op.SSTORE(1, Op.TIMESTAMP)
        + Op.SSTORE(2, Op.COINBASE)
        + Op.SSTORE(3, Op.PREVRANDAO)
        + Op.SSTORE(4, Op.BASEFEE)
        + Op.SSTORE(5, Op.GASLIMIT)
        + Op.STOP
    )
)
"""
Record the block context the caller overrode.

Every one of these lands in storage, and storage lands in the state
root, so a client that resolved a `blockOverrides` field differently
produces a different block hash rather than a quietly different answer.
"""

FORWARDER_CODE = Bytes(
    bytes(
        Op.LOG0(0, 0)
        + Op.POP(Op.CALL(Op.GAS, Op.CALLDATALOAD(0), 1, 0, 0, 0, 0))
        + Op.STOP
    )
)
"""
Log, then pass one wei on to whoever calldata names.

The interleaving is the point: `traceTransfers` has to report the
caller's transfer, then this log, then this transfer, in that order.
"""

SELF_DESTRUCTOR_CODE = Bytes(bytes(Op.SELFDESTRUCT(Op.CALLDATALOAD(0))))

BLOCKHASH_READER_CODE = Bytes(
    bytes(Op.MSTORE(0, Op.BLOCKHASH(Op.CALLDATALOAD(0))) + Op.RETURN(0, 32))
)

GAS_BURNER_CODE = Bytes(bytes(Op.JUMPDEST + Op.JUMP(0)))
"""Loop until the gas runs out, for the out-of-gas case."""

ALLOCATION: Tuple[Allocation, ...] = (
    Allocation(SENDER, 10**18),
    Allocation(PAUPER, 0),
    Allocation(EMPTY_ACCOUNT_ADDRESS, 0),
    Allocation(LOGGER, 0, LOGGER_CODE),
    Allocation(REVERTER, 0, REVERTER_CODE),
    Allocation(CONTEXT_READER, 0, CONTEXT_READER_CODE),
    Allocation(FORWARDER, 10**9, FORWARDER_CODE),
    Allocation(SELF_DESTRUCTOR, 10**9, SELF_DESTRUCTOR_CODE),
    Allocation(BLOCKHASH_READER, 0, BLOCKHASH_READER_CODE),
    Allocation(GAS_BURNER, 0, GAS_BURNER_CODE),
)


def genesis_json() -> Dict[str, Any]:
    """Render the genesis in the form `geth init` reads."""
    return {
        "config": {
            "chainId": int(CHAIN_ID),
            "homesteadBlock": 0,
            "eip150Block": 0,
            "eip155Block": 0,
            "eip158Block": 0,
            "byzantiumBlock": 0,
            "constantinopleBlock": 0,
            "petersburgBlock": 0,
            "istanbulBlock": 0,
            "berlinBlock": 0,
            "londonBlock": 0,
            "mergeNetsplitBlock": 0,
            "shanghaiTime": 0,
            "cancunTime": 0,
            "terminalTotalDifficulty": 0,
            "blobSchedule": {
                "cancun": {
                    "target": 3,
                    "max": 6,
                    "baseFeeUpdateFraction": 3338477,
                }
            },
        },
        "nonce": "0x0",
        "timestamp": "0x0",
        "extraData": "0x",
        "gasLimit": hex(int(GAS_LIMIT)),
        "difficulty": "0x0",
        "mixHash": "0x" + "00" * 32,
        "coinbase": "0x" + "00" * 20,
        "baseFeePerGas": hex(int(BASE_FEE_PER_GAS)),
        "excessBlobGas": "0x0",
        "blobGasUsed": "0x0",
        "alloc": {
            entry.address: {
                "balance": hex(entry.balance),
                **({"code": "0x" + entry.code.hex()} if entry.code else {}),
            }
            for entry in ALLOCATION
        },
    }


def genesis_state() -> State:
    """Render the genesis as the state the specification executes on."""
    state = State()
    for entry in ALLOCATION:
        code_hash = (
            store_code(state, entry.code) if entry.code else EMPTY_CODE_HASH
        )
        set_account(
            state,
            _address(entry.address),
            Account(
                nonce=Uint(0),
                balance=U256(entry.balance),
                code_hash=code_hash,
            ),
        )
    return state


def genesis_header(fork: Optional[SimulateFork] = None) -> Any:
    """
    Build the genesis header the specification commits to.

    Genesis is sui generis, so this is not the fork's own block
    production: it is the same set of fields `geth init` writes, hashed
    the ordinary way. Its only job is to give the harness a parent hash
    it derived rather than one it was told.
    """
    fork = fork or resolve_simulate_fork(FORK_NAME)
    return fork.header(
        parent_hash=Hash32(b"\0" * 32),
        ommers_hash=EMPTY_OMMERS_HASH,
        coinbase=Bytes20(b"\0" * 20),
        state_root=state_root(genesis_state()),
        transactions_root=EMPTY_TRIE_ROOT,
        receipt_root=EMPTY_TRIE_ROOT,
        bloom=b"\0" * 256,
        difficulty=Uint(0),
        number=Uint(0),
        gas_limit=GAS_LIMIT,
        gas_used=Uint(0),
        timestamp=U256(0),
        prev_randao=b"\0" * 32,
        base_fee_per_gas=BASE_FEE_PER_GAS,
        withdrawals_root=EMPTY_TRIE_ROOT,
        blob_gas_used=U64(0),
        excess_blob_gas=U64(0),
        parent_beacon_block_root=Hash32(b"\0" * 32),
    )


def genesis_hash() -> Hash32:
    """Return the genesis block hash the specification derives."""
    return keccak256(rlp.encode(genesis_header()))


def base_block() -> BaseBlock:
    """Return the head a simulation starts from: genesis itself."""
    return BaseBlock(
        number=Uint(0),
        timestamp=U256(0),
        gas_limit=GAS_LIMIT,
        base_fee_per_gas=BASE_FEE_PER_GAS,
        excess_blob_gas=U64(0),
        block_hash=genesis_hash(),
    )


def contract_addresses() -> List[str]:
    """Return every address the allocation gives code to."""
    return [entry.address for entry in ALLOCATION if entry.code]
