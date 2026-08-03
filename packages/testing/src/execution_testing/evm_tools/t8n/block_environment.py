"""
Build the spec's per-fork ``BlockEnvironment`` from a testing-package
``Environment``.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, List, Optional

from ethereum.crypto.hash import Hash32, keccak256
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes8, Bytes20, Bytes32, Bytes256
from ethereum_types.numeric import U64, U256, Uint

if TYPE_CHECKING:
    from ethereum_spec_tools.loaders.fork_loader import ForkLoad

    from execution_testing.test_types import Environment as TestingEnvironment


@dataclass
class Ommer:
    """
    Pre-PoS ommer header summary consumed by `pay_block_rewards`.

    Carries the two fields needed for ommer-reward arithmetic
    (`block_number - delta` and the ommer coinbase). The testing
    `Environment.ommers` field is `List[Hash]` and cannot represent
    these — the JSON CLI fallback populates this from the raw env JSON
    instead, and the in-process path leaves it empty (PoS has no ommers).
    """

    delta: str
    address: Bytes20


def build_block_environment(
    fork: "ForkLoad",
    env: "TestingEnvironment",
    pre_state: Any,
    chain_id: U64,
    state_test: bool = False,
) -> Any:
    """
    Build the fork's `BlockEnvironment` from a testing `Environment`.

    `pre_state` must satisfy the spec's `PreState` protocol (in
    practice, a testing `Alloc`).
    """
    block_state = fork.BlockState(pre_state=pre_state)

    block_number = Uint(int(env.number))
    block_gas_limit = Uint(int(env.gas_limit))
    block_timestamp = U256(int(env.timestamp))
    coinbase = Bytes20(env.fee_recipient)

    base_fee_per_gas = _resolve_base_fee_per_gas(env, fork, block_gas_limit)

    kw_arguments: dict[str, Any] = {
        "block_hashes": _resolve_block_hashes(env.block_hashes, block_number),
        "coinbase": coinbase,
        "number": block_number,
        "time": block_timestamp,
        "block_gas_limit": block_gas_limit,
        "chain_id": chain_id,
        "state": block_state,
    }

    if fork.has_calculate_base_fee_per_gas:
        assert base_fee_per_gas is not None
        kw_arguments["base_fee_per_gas"] = base_fee_per_gas

    if fork.hardfork.consensus.is_pos():
        kw_arguments["prev_randao"] = _resolve_prev_randao(env)
    else:
        kw_arguments["difficulty"] = _resolve_block_difficulty(
            env, fork, block_number, block_timestamp
        )

    if fork.has_beacon_roots_address:
        kw_arguments["parent_beacon_block_root"] = (
            None if state_test else _resolve_parent_beacon_block_root(env)
        )
        kw_arguments["excess_blob_gas"] = _resolve_excess_blob_gas(env, fork)

    if fork.has_hash_block_access_list:
        kw_arguments["block_access_list_builder"] = (
            fork.BlockAccessListBuilder()
        )

    if fork.has_slot_number:
        slot_number = env.slot_number
        kw_arguments["slot_number"] = (
            U64(int(slot_number)) if slot_number is not None else None
        )

    return fork.BlockEnvironment(**kw_arguments)


def _resolve_base_fee_per_gas(
    env: "TestingEnvironment", fork: "ForkLoad", block_gas_limit: Uint
) -> Optional[Uint]:
    """Use ``currentBaseFee`` if present; otherwise derive from parent."""
    if not fork.has_calculate_base_fee_per_gas:
        return None
    if env.base_fee_per_gas is not None:
        return Uint(int(env.base_fee_per_gas))
    assert env.parent_gas_limit is not None
    assert env.parent_gas_used is not None
    assert env.parent_base_fee_per_gas is not None
    return fork.calculate_base_fee_per_gas(
        block_gas_limit,
        Uint(int(env.parent_gas_limit)),
        Uint(int(env.parent_gas_used)),
        Uint(int(env.parent_base_fee_per_gas)),
    )


def _resolve_excess_blob_gas(
    env: "TestingEnvironment",
    fork: "ForkLoad",
) -> Optional[U64]:
    """Use ``currentExcessBlobGas`` if present; else derive from parent."""
    if env.excess_blob_gas is not None:
        return U64(int(env.excess_blob_gas))

    parent_blob_gas_used = U64(
        int(env.parent_blob_gas_used) if env.parent_blob_gas_used else 0
    )
    parent_excess_blob_gas = U64(
        int(env.parent_excess_blob_gas) if env.parent_excess_blob_gas else 0
    )
    # EIP-7918 reads ``parent.base_fee_per_gas`` from the parent header.
    parent_base_fee_per_gas = Uint(
        int(env.parent_base_fee_per_gas)
        if env.parent_base_fee_per_gas is not None
        else 0
    )

    arguments: dict[str, Any] = {
        "parent_hash": Hash32(b"\0" * 32),
        "ommers_hash": Hash32(b"\0" * 32),
        "coinbase": Bytes20(b"\0" * 20),
        "state_root": Hash32(b"\0" * 32),
        "transactions_root": Hash32(b"\0" * 32),
        "receipt_root": Hash32(b"\0" * 32),
        "bloom": Bytes256(b"\0" * 256),
        "difficulty": Uint(0),
        "number": Uint(0),
        "gas_limit": Uint(0),
        "gas_used": Uint(0),
        "timestamp": U256(0),
        "extra_data": b"",
        "prev_randao": Bytes32(b"\0" * 32),
        "nonce": Bytes8(b"\0" * 8),
        "withdrawals_root": Hash32(b"\0" * 32),
        "parent_beacon_block_root": Hash32(b"\0" * 32),
        "base_fee_per_gas": parent_base_fee_per_gas,
        "blob_gas_used": parent_blob_gas_used,
        "excess_blob_gas": parent_excess_blob_gas,
    }
    if fork.has_compute_requests_hash:
        arguments["requests_hash"] = Hash32(b"\0" * 32)
    if fork.has_hash_block_access_list:
        arguments["block_access_list_hash"] = Hash32(b"\0" * 32)
    if fork.has_slot_number:
        arguments["slot_number"] = U64(0)

    parent_header = fork.Header(**arguments)
    return fork.calculate_excess_blob_gas(parent_header)


def _resolve_block_difficulty(
    env: "TestingEnvironment",
    fork: "ForkLoad",
    block_number: Uint,
    block_timestamp: U256,
) -> Optional[Uint]:
    """Use ``currentDifficulty`` if present; otherwise derive from parent."""
    if env.difficulty is not None:
        return Uint(int(env.difficulty))

    assert env.parent_timestamp is not None
    assert env.parent_difficulty is not None
    args: List[Any] = [
        block_number,
        block_timestamp,
        U256(int(env.parent_timestamp)),
        Uint(int(env.parent_difficulty)),
    ]
    if fork.calculate_block_difficulty_arity > 4:
        empty_ommers_hash = keccak256(rlp.encode([]))
        parent_ommers_hash = Hash32(env.parent_ommers_hash)
        args.append(parent_ommers_hash != empty_ommers_hash)
    return fork.calculate_block_difficulty(*args)


def _resolve_prev_randao(env: "TestingEnvironment") -> Bytes32:
    """Pad the (numeric) ``prev_randao`` field to 32 bytes."""
    value = env.prev_randao
    if value is None:
        return Bytes32(b"\0" * 32)
    return Bytes32(int(value).to_bytes(32, "big"))


def _resolve_block_hashes(
    block_hashes: Any, block_number: Uint
) -> List[Optional[Hash32]]:
    """
    Return up to the last 256 block hashes preceding ``block_number``.

    `block_hashes` is the testing `Environment.block_hashes` dict keyed by
    block number; missing entries become `None` placeholders.
    """
    result: List[Optional[Hash32]] = []
    if not block_hashes:
        return result
    normalized = {int(k): Hash32(v) for k, v in block_hashes.items()}
    max_blockhash_count = min(Uint(256), block_number)
    for number in range(
        int(block_number) - int(max_blockhash_count), int(block_number)
    ):
        result.append(normalized.get(number))
    return result


def _resolve_parent_beacon_block_root(
    env: "TestingEnvironment",
) -> Optional[Hash32]:
    """Return the parent beacon block root, or ``None`` if absent."""
    if env.parent_beacon_block_root is None:
        return None
    return Hash32(env.parent_beacon_block_root)
