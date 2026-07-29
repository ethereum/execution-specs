"""
Measure the gas cost of every SSTORE transition class (cold/warm x
original/current/new value combinations) via inline GAS deltas (by Ori
Pomerantz qbzzt1@gmail.com).

Ported from:
state_tests/stSStoreTest/sstoreGasFiller.yml

@manually-enhanced: Do not overwrite. The nine measured transition costs
are derived from SSTORE opcode metadata instead of pinned numbers, so
EIP-8037's state-gas repricing (and any future one) is tracked
automatically; the explicit gas limit equals the EIP-7825 cap, so the
state gas spills into the measured deltas.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSStoreTest/sstoreGasFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_sstore_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Measure each SSTORE transition's gas against opcode metadata."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xBA1A9CE0BA1A9CE, nonce=1)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: yul
    # berlin
    # {
    #    // Use storage of 0x1000 and above for gas figures
    #    let storageLoc := 0x1000
    #
    #    // Gas spent on the measurement (two PUSHs, GAS, and SWAPs as
    #    // needed for the variables)
    #    let measureGas := 8
    #
    #    let gas0, gas1
    #
    #    // Cold storage, non-zero to non-zero
    #    gas0 := gas()
    #    sstore(0, 0xBEEF)
    #    gas1 := gas()
    #    sstore(storageLoc, sub(sub(gas0, gas1), measureGas))
    #    storageLoc := add(storageLoc, 1)
    #
    #    // Warm storage, non-zero to non-zero
    #    gas0 := gas()
    #    sstore(0, 0xDEADBEEF)
    #    gas1 := gas()
    #    sstore(storageLoc, sub(sub(gas0, gas1), measureGas))
    #    storageLoc := add(storageLoc, 1)
    #
    #    // Warm storage, non-zero to zero
    #    gas0 := gas()
    #    sstore(0, 0)
    #    gas1 := gas()
    #    sstore(storageLoc, sub(sub(gas0, gas1), measureGas))
    # ... (50 more lines)
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x1]
        + Op.PUSH1[0x8]
        + Op.DUP2
        + Op.DUP1 * 7
        + Op.PUSH2[0x1000]
        + Op.DUP10
        + Op.GAS
        + Op.SSTORE(key=0x0, value=0xBEEF)
        + Op.GAS
        + Op.SWAP1
        + Op.SUB
        + Op.SSTORE(key=Op.DUP2, value=Op.SUB)
        + Op.ADD
        + Op.DUP9
        + Op.GAS
        + Op.SSTORE(key=0x0, value=0xDEADBEEF)
        + Op.GAS
        + Op.SWAP1
        + Op.SUB
        + Op.SSTORE(key=Op.DUP2, value=Op.SUB)
        + Op.ADD
        + Op.DUP8
        + Op.GAS
        + Op.SSTORE(key=Op.DUP1, value=0x0)
        + Op.GAS
        + Op.SWAP1
        + Op.SUB
        + Op.SSTORE(key=Op.DUP2, value=Op.SUB)
        + Op.ADD
        + Op.DUP7
        + Op.GAS
        + Op.SSTORE(key=Op.DUP1, value=0x0)
        + Op.GAS
        + Op.SWAP1
        + Op.SUB
        + Op.SSTORE(key=Op.DUP2, value=Op.SUB)
        + Op.ADD
        + Op.DUP6
        + Op.GAS
        + Op.SSTORE(key=0x0, value=0x1234)
        + Op.GAS
        + Op.SWAP1
        + Op.SUB
        + Op.SSTORE(key=Op.DUP2, value=Op.SUB)
        + Op.ADD
        + Op.DUP5
        + Op.GAS
        + Op.SSTORE(key=Op.DUP5, value=0x0)
        + Op.GAS
        + Op.SWAP1
        + Op.SUB
        + Op.SSTORE(key=Op.DUP2, value=Op.SUB)
        + Op.ADD
        + Op.DUP4
        + Op.GAS
        + Op.SSTORE(key=0x2, value=0x60A7)
        + Op.GAS
        + Op.SWAP1
        + Op.SUB
        + Op.SSTORE(key=Op.DUP2, value=Op.SUB)
        + Op.ADD
        + Op.DUP3
        + Op.GAS
        + Op.SSTORE(key=0x3, value=0x0)
        + Op.GAS
        + Op.SWAP1
        + Op.SUB
        + Op.SSTORE(key=Op.DUP2, value=Op.SUB)
        + Op.ADD
        + Op.SWAP1
        + Op.GAS
        + Op.SSTORE(key=0x3, value=0x60A7)
        + Op.GAS
        + Op.SWAP1
        + Op.SUB
        + Op.SSTORE(key=Op.DUP2, value=Op.SUB)
        + Op.POP * 2
        + Op.SSTORE(key=Op.DUP1, value=0x0)
        + Op.SSTORE(key=0x1, value=0x0)
        + Op.SSTORE(key=0x2, value=0x0)
        + Op.SSTORE(key=0x3, value=0x0)
        + Op.STOP,
        storage={0: 24743, 1: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=16777216,
        nonce=1,
    )

    # The measured transitions, in bytecode order (slots 0 and 1 start at
    # 24743; slots 2 and 3 start empty). Each stored delta is the pure
    # SSTORE cost (the contract subtracts its own 8-gas overhead).
    transitions = [
        # slot 0: cold, original nonzero -> different nonzero
        dict(key_warm=False, original_value=24743, new_value=0xBEEF),
        # slot 0: warm dirty, nonzero -> nonzero
        dict(
            key_warm=True,
            original_value=24743,
            current_value=0xBEEF,
            new_value=0xDEADBEEF,
        ),
        # slot 0: warm dirty, nonzero -> zero
        dict(
            key_warm=True,
            original_value=24743,
            current_value=0xDEADBEEF,
            new_value=0,
        ),
        # slot 0: warm dirty, zero -> zero
        dict(
            key_warm=True, original_value=24743, current_value=0, new_value=0
        ),
        # slot 0: warm dirty, zero -> nonzero
        dict(
            key_warm=True,
            original_value=24743,
            current_value=0,
            new_value=0x1234,
        ),
        # slot 1: cold, original nonzero -> zero
        dict(key_warm=False, original_value=24743, new_value=0),
        # slot 2: cold fresh, zero -> nonzero
        dict(key_warm=False, original_value=0, new_value=0x60A7),
        # slot 3: cold fresh, zero -> zero
        dict(key_warm=False, original_value=0, new_value=0),
        # slot 3: warm fresh, zero -> nonzero
        dict(key_warm=True, original_value=0, new_value=0x60A7),
    ]
    post = {
        target: Account(
            storage={
                0x1000 + i: Op.SSTORE.with_metadata(**md).gas_cost(fork)
                for i, md in enumerate(transitions)
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
