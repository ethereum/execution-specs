"""
create fails because init code has undefined opcode, trying to suicide to it.

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest
createInitFailUndefinedInstructionFiller.json
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
    [
        "tests/static/state_tests/stCallCreateCallCodeTest/createInitFailUndefinedInstructionFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_init_fail_undefined_instruction(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Create fails because init code has undefined opcode, trying to..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x0, value=0xF9)
            + Op.SELFDESTRUCT(
                address=Op.CREATE2(value=0x1, offset=0x0, size=0x1, salt=0x0),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0183feb7335d767d4d6ae41bbdea7afb27227860"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x0, value=0xF9)
            + Op.SELFDESTRUCT(
                address=Op.CREATE(value=0x1, offset=0x0, size=0x1)
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x552f200b75457440ee6df9159d6b188e9d18c222"),  # noqa: E501
    )
    # Source: LLL
    # { [[0]] (CALL 400000 <contract:0x1000000000000000000000000000000000000000> 0 0 0 0 0) [[1]] (CALL 400000 <contract:0x2000000000000000000000000000000000000000> 0 0 0 0 0) [[2]] 1 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x61A80,
                    address=0x552F200B75457440EE6DF9159D6B188E9D18C222,
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
                    address=0x183FEB7335D767D4D6AE41BBDEA7AFB27227860,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x73e58ff0ab0c422709d507efb9d4889740040144"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=900000,
        value=100000,
    )

    post = {
        contract: Account(storage={2: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
