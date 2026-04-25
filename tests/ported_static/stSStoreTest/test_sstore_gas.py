"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stSStoreTest/sstoreGasFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
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
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
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

    post = {
        target: Account(
            storage={
                4096: 5000,
                4097: 100,
                4098: 100,
                4099: 100,
                4100: 100,
                4101: 5000,
                4102: 22100,
                4103: 2200,
                4104: 20000,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
