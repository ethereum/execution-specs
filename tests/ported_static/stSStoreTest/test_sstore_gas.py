"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/stSStoreTest/sstoreGasFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
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
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x48dc5a9f099caaaa557742ca3a990a94be45b9969126a1bc74e5e8be5a2b5b47
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
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
    target = pre.deploy_contract(
        code=Op.PUSH1[0x1] + Op.PUSH1[0x8] + Op.DUP2 + Op.DUP1 * 7
        + Op.PUSH2[0x1000] + Op.DUP10 + Op.GAS + Op.SSTORE(key=0x0, value=0xbeef)  # noqa: E501
        + Op.GAS + Op.SWAP1 + Op.SUB + Op.SSTORE(key=Op.DUP2, value=Op.SUB)
        + Op.ADD + Op.DUP9 + Op.GAS + Op.SSTORE(key=0x0, value=0xdeadbeef)
        + Op.GAS + Op.SWAP1 + Op.SUB + Op.SSTORE(key=Op.DUP2, value=Op.SUB)
        + Op.ADD + Op.DUP8 + Op.GAS + Op.SSTORE(key=Op.DUP1, value=0x0) + Op.GAS  # noqa: E501
        + Op.SWAP1 + Op.SUB + Op.SSTORE(key=Op.DUP2, value=Op.SUB) + Op.ADD
        + Op.DUP7 + Op.GAS + Op.SSTORE(key=Op.DUP1, value=0x0) + Op.GAS
        + Op.SWAP1 + Op.SUB + Op.SSTORE(key=Op.DUP2, value=Op.SUB) + Op.ADD
        + Op.DUP6 + Op.GAS + Op.SSTORE(key=0x0, value=0x1234) + Op.GAS + Op.SWAP1  # noqa: E501
        + Op.SUB + Op.SSTORE(key=Op.DUP2, value=Op.SUB) + Op.ADD + Op.DUP5
        + Op.GAS + Op.SSTORE(key=Op.DUP5, value=0x0) + Op.GAS + Op.SWAP1 + Op.SUB  # noqa: E501
        + Op.SSTORE(key=Op.DUP2, value=Op.SUB) + Op.ADD + Op.DUP4 + Op.GAS
        + Op.SSTORE(key=0x2, value=0x60a7) + Op.GAS + Op.SWAP1 + Op.SUB
        + Op.SSTORE(key=Op.DUP2, value=Op.SUB) + Op.ADD + Op.DUP3 + Op.GAS
        + Op.SSTORE(key=0x3, value=0x0) + Op.GAS + Op.SWAP1 + Op.SUB
        + Op.SSTORE(key=Op.DUP2, value=Op.SUB) + Op.ADD + Op.SWAP1 + Op.GAS
        + Op.SSTORE(key=0x3, value=0x60a7) + Op.GAS + Op.SWAP1 + Op.SUB
        + Op.SSTORE(key=Op.DUP2, value=Op.SUB) + Op.POP * 2
        + Op.SSTORE(key=Op.DUP1, value=0x0) + Op.SSTORE(key=0x1, value=0x0)
        + Op.SSTORE(key=0x2, value=0x0) + Op.SSTORE(key=0x3, value=0x0) + Op.STOP,  # noqa: E501
        storage={0: 24743, 1: 24743},
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x84e1dc6705b8b9b7ffaca256c9266792bdd0943b"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=1)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=16777216,
        nonce=1,
        gas_price=10,
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
