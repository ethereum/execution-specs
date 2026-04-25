"""
Test_stack_limit_gas_1024.

Ported from:
state_tests/stMemoryTest/stackLimitGas_1024Filler.json
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
    ["state_tests/stMemoryTest/stackLimitGas_1024Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_stack_limit_gas_1024(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_stack_limit_gas_1024."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x6400000000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=42949672960,
    )

    # Source: lll
    # (asm 1022 0x00 MSTORE JUMPDEST GAS 0x01 0x00 MLOAD SUB 0x00 MSTORE 0x00 MLOAD 0x06 JUMPI STOP )  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x3FE)
        + Op.JUMPDEST
        + Op.GAS
        + Op.MSTORE(offset=0x0, value=Op.SUB(Op.MLOAD(offset=0x0), 0x1))
        + Op.JUMPI(pc=0x6, condition=Op.MLOAD(offset=0x0))
        + Op.STOP * 2,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
        value=10,
    )

    post = {
        target: Account(
            storage={},
            code=bytes.fromhex(
                "6103fe6000525b5a6001600051036000526000516006570000"
            ),
            nonce=0,
        ),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
