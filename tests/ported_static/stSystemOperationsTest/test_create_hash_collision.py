"""
Test_create_hash_collision.

Ported from:
state_tests/stSystemOperationsTest/CreateHashCollisionFiller.json
"""

import pytest
from execution_testing import (
    EOA,
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
    ["state_tests/stSystemOperationsTest/CreateHashCollisionFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_hash_collision(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_hash_collision."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
    contract_1 = Address(0xD2571607E241ECF590ED94B12D87C94BABE36DB6)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # { (MSTORE 0 0x601080600c6000396000f3006000355415600957005b60203560003555) [[ 0 ]] (CREATE 23 3 29) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x601080600C6000396000F3006000355415600957005B60203560003555,
        )
        + Op.SSTORE(
            key=0x0, value=Op.CREATE(value=0x17, offset=0x3, size=0x1D)
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw
    # 0x60016001016055
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.ADD(0x1, 0x1) + Op.PUSH1[0x55],
        balance=42,
        nonce=0,
        address=Address(0xD2571607E241ECF590ED94B12D87C94BABE36DB6),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=10000000,
        value=0x186A0,
    )

    post = {
        contract_0: Account(storage={0: 0}),
        contract_1: Account(
            storage={},
            code=bytes.fromhex("60016001016055"),
            balance=42,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
