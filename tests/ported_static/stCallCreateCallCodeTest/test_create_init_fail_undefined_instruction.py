"""
create fails because init code has undefined opcode, trying to suicide to it

Ported from:
state_tests/stCallCreateCallCodeTest/createInitFailUndefinedInstructionFiller.json
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
    ["state_tests/stCallCreateCallCodeTest/createInitFailUndefinedInstructionFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_init_fail_undefined_instruction(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """create fails because init code has undefined opcode, trying to suic..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    # Source: lll
    # { [[0]] (CALL 400000 <contract:0x1000000000000000000000000000000000000000> 0 0 0 0 0) [[1]] (CALL 400000 <contract:0x2000000000000000000000000000000000000000> 0 0 0 0 0) [[2]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=0x61a80, address=0x552f200b75457440ee6df9159d6b188e9d18c222, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=Op.CALL(gas=0x61a80, address=0x183feb7335d767d4d6ae41bbdea7afb27227860, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x73e58ff0ab0c422709d507efb9d4889740040144"),  # noqa: E501
    )
    # Source: lll
    # {(MSTORE8 0 0xf9 ) (SELFDESTRUCT (CREATE 1 0 1)) }
    addr_0x1000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.MSTORE8(offset=0x0, value=0xf9)
        + Op.SELFDESTRUCT(address=Op.CREATE(value=0x1, offset=0x0, size=0x1))
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x552f200b75457440ee6df9159d6b188e9d18c222"),  # noqa: E501
    )
    # Source: lll
    # {(MSTORE8 0 0xf9 ) (SELFDESTRUCT (CREATE2 1 0 1 0)) }
    addr_0x2000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.MSTORE8(offset=0x0, value=0xf9)
        + Op.SELFDESTRUCT(address=Op.CREATE2(value=0x1, offset=0x0, size=0x1, salt=0x0))
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x0183feb7335d767d4d6ae41bbdea7afb27227860"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=900000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={2: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
