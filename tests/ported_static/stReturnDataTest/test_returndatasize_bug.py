"""
RETURNDATASIZE after a failing CALL (due to insufficient balance)...

Ported from:
state_tests/stReturnDataTest/returndatasize_bugFiller.json
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
    ["state_tests/stReturnDataTest/returndatasize_bugFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatasize_bug(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """RETURNDATASIZE after a failing CALL (due to insufficient balance)..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x834185262E53584684BF2B72C64E510013C235D0F45E462DB65900455DF45A35
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    # Source: lll
    # { (CALL 1 <contract:0x1f572e5295c57f15886f9b263e2f6d2d6c7b5ec6> 50000 0 0 0 0) (SSTORE 0 (RETURNDATASIZE)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x1,
                address=0xA6DE4978FAA392285CC6411DFE442872304DEB1,
                value=0xC350,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.STOP,
        storage={0: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x0D7BC2FBD330F7D4EC71764551A8B9CFB11619F5),  # noqa: E501
    )
    # Source: lll
    # { (CALL 10 1 50000 0 0 0 0) (SSTORE 1 1) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0xA,
                address=0x1,
                value=0xC350,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0x0A6DE4978FAA392285CC6411DFE442872304DEB1),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {
        target: Account(storage={0: 0}),
        addr: Account(storage={1: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
