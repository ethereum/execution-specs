"""Unit tests for Amsterdam ``calculate_excess_blob_gas``."""

from typing import Type

import pytest
from ethereum_types.bytes import Bytes8, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.forks.amsterdam.fork_types import Bloom
from ethereum.forks.amsterdam.vm.gas import GasCosts, calculate_excess_blob_gas
from ethereum.forks.bpo2.blocks import Header as BPO2Header
from ethereum.forks.bpo5.blocks import Header as BPO5Header
from ethereum.state import Address

ZERO_HASH = Hash32(b"\0" * 32)


@pytest.mark.parametrize(
    "header_class", [BPO2Header, BPO5Header], ids=["bpo2", "bpo5"]
)
def test_excess_blob_gas_from_previous_fork(
    header_class: Type[BPO2Header] | Type[BPO5Header],
) -> None:
    """Carry excess blob gas over from any fork that precedes Amsterdam."""
    target = GasCosts.BLOB_TARGET_GAS_PER_BLOCK
    blob_gas_used = target * U64(2)
    parent = header_class(
        parent_hash=ZERO_HASH,
        ommers_hash=ZERO_HASH,
        coinbase=Address(b"\0" * 20),
        state_root=ZERO_HASH,
        transactions_root=ZERO_HASH,
        receipt_root=ZERO_HASH,
        bloom=Bloom(b"\0" * 256),
        difficulty=Uint(0),
        number=Uint(1),
        gas_limit=Uint(30_000_000),
        gas_used=Uint(0),
        timestamp=U256(14_999),
        extra_data=b"",
        prev_randao=Bytes32(b"\0" * 32),
        nonce=Bytes8(b"\0" * 8),
        base_fee_per_gas=Uint(7),
        withdrawals_root=ZERO_HASH,
        blob_gas_used=blob_gas_used,
        excess_blob_gas=U64(0),
        parent_beacon_block_root=ZERO_HASH,
        requests_hash=ZERO_HASH,
    )

    excess_blob_gas = calculate_excess_blob_gas(parent)  # type: ignore[arg-type]

    assert excess_blob_gas == target
