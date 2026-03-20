"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stSStoreTest/sstoreGasFiller.yml
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stSStoreTest/sstoreGasFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_sstore_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x48DC5A9F099CAAAA557742CA3A990A94BE45B9969126A1BC74E5E8BE5A2B5B47
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
    # Source: Yul
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
    #    storageLoc := add(storageLoc, 1)
    # ... (49 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.PUSH1[0x1]
            + Op.PUSH1[0x8]
            + Op.DUP2
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
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
            + Op.POP
            + Op.POP
            + Op.SSTORE(key=Op.DUP1, value=0x0)
            + Op.SSTORE(key=0x1, value=0x0)
            + Op.SSTORE(key=0x2, value=0x0)
            + Op.SSTORE(key=0x3, value=0x0)
            + Op.STOP
        ),
        storage={0x0: 0x60A7, 0x1: 0x60A7},
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x84e1dc6705b8b9b7ffaca256c9266792bdd0943b"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
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
                    code=bytes.fromhex(
                        "600160088180808080808080611000895a61beef6000555a900303815501885a63deadbeef6000555a900303815501875a600080555a900303815501865a600080555a900303815501855a6112346000555a900303815501845a600084555a900303815501835a6160a76002555a900303815501825a60006003555a900303815501905a6160a76003555a900303815550506000805560006001556000600255600060035500"  # noqa: E501
                    ),
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=16777216,
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
