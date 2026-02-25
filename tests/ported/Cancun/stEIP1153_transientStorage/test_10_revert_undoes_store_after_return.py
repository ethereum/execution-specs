"""
Revert undoes the transient storage writes after a successful call.

Ported from:
tests/static/state_tests/Cancun/stEIP1153_transientStorage/10_revertUndoesStoreAfterReturnFiller.yml

contract code:
    push0
    calldataload
    push1 0xe0
    shr
    dup1
    push4 0x70ac643e
    eq
    push1 0x2f
    jumpi
    dup1
    push4 0x76b85d23
    eq
    push1 0x2b
    jumpi
    push4 0x4ccca553
    eq
    push1 0x23
    jumpi
    stop
    jumpdest
    ... (66 more instructions)
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/Cancun/stEIP1153_transientStorage/10_revertUndoesStoreAfterReturnFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_10_revert_undoes_store_after_return(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Revert undoes the transient storage writes after a successful call.."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xcef5f3b33e31360216fab2c61046840df9bd788e")
    contract = Address("0xe42b9e92d5348b0fc6353d40e3d220c316d3c685")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4503599627370496,
    )

    pre[sender] = Account(balance=0x3635c9adc5dea00000, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH0 + Op.CALLDATALOAD + Op.PUSH1[0xe0] + Op.SHR + Op.DUP1
        + Op.PUSH4[0x70ac643e] + Op.EQ + Op.PUSH1[0x2f] + Op.JUMPI + Op.DUP1
        + Op.PUSH4[0x76b85d23] + Op.EQ + Op.PUSH1[0x2b] + Op.JUMPI
        + Op.PUSH4[0x4ccca553] + Op.EQ + Op.PUSH1[0x23] + Op.JUMPI + Op.STOP
        + Op.JUMPDEST + Op.PUSH1[0x29] + Op.PUSH1[0x76] + Op.JUMP + Op.JUMPDEST
        + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x5c] + Op.JUMP + Op.JUMPDEST + Op.POP
        + Op.PUSH1[0x29] + Op.PUSH1[0x5] + Op.PUSH0 + Op.TSTORE + Op.PUSH0 + Op.TLOAD
        + Op.PUSH0 + Op.SSTORE + Op.PUSH4[0x76b85d23] + Op.PUSH1[0xe0] + Op.SHL
        + Op.PUSH0 + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH0 + Op.DUP2 + Op.DUP2
        + Op.DUP1 + Op.ADDRESS + Op.GAS + Op.CALL + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH0 + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH0 + Op.TLOAD
        + Op.PUSH1[0x3] + Op.SSTORE + Op.JUMP + Op.JUMPDEST + Op.PUSH4[0x4ccca553]
        + Op.PUSH1[0xe0] + Op.SHL + Op.PUSH0 + Op.MSTORE + Op.PUSH0 + Op.DUP1
        + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.ADDRESS + Op.GAS + Op.CALL
        + Op.PUSH0 + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH0 + Op.REVERT + Op.JUMPDEST
        + Op.PUSH1[0x6] + Op.PUSH0 + Op.TSTORE + Op.JUMP
    ),
        storage={0x1: 0xffff},
    )

    tx = Transaction(
        secret_key=Hash(
            "0xbe0e7d5fea1604bf57e004b0b414df8de04816dbb1c8f8719b725d0d6619b531"
        ),
        to=contract,
        data=bytes.fromhex("70ac643e"),
        gas_limit=400000,
        max_fee_per_gas=2000,
        max_priority_fee_per_gas=0,
        nonce=0,
        value=0,
        access_list=[],
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
