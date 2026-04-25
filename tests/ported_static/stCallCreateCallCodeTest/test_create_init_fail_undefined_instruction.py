"""
Create fails because init code has undefined opcode, trying to suicide...

Ported from:
state_tests/stCallCreateCallCodeTest/createInitFailUndefinedInstructionFiller.json
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
    [
        "state_tests/stCallCreateCallCodeTest/createInitFailUndefinedInstructionFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_init_fail_undefined_instruction(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Create fails because init code has undefined opcode, trying to..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    # Source: lll
    # {(MSTORE8 0 0xf9 ) (SELFDESTRUCT (CREATE 1 0 1)) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x0, value=0xF9)
        + Op.SELFDESTRUCT(address=Op.CREATE(value=0x1, offset=0x0, size=0x1))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )
    # Source: lll
    # {(MSTORE8 0 0xf9 ) (SELFDESTRUCT (CREATE2 1 0 1 0)) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x0, value=0xF9)
        + Op.SELFDESTRUCT(
            address=Op.CREATE2(value=0x1, offset=0x0, size=0x1, salt=0x0)
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )
    # Source: lll
    # { [[0]] (CALL 400000 <contract:0x1000000000000000000000000000000000000000> 0 0 0 0 0) [[1]] (CALL 400000 <contract:0x2000000000000000000000000000000000000000> 0 0 0 0 0) [[2]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x61A80,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=0x61A80,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=900000,
        value=0x186A0,
    )

    post = {target: Account(storage={2: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
