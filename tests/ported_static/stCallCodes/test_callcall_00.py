"""
call -> call -> code, params check.

Ported from:
tests/static/state_tests/stCallCodes/callcall_00Filler.json
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
    ["tests/static/state_tests/stCallCodes/callcall_00Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcall_00(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Call -> call -> code, params check."""
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
        gas_limit=30000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x2, value=0x1)
            + Op.SSTORE(key=0x4, value=Op.CALLER)
            + Op.SSTORE(key=0x7, value=Op.CALLVALUE)
            + Op.SSTORE(key=0xE6, value=Op.ADDRESS)
            + Op.SSTORE(key=0xE8, value=Op.ORIGIN)
            + Op.SSTORE(key=0xEC, value=Op.CALLDATASIZE)
            + Op.SSTORE(key=0xEE, value=Op.CODESIZE)
            + Op.SSTORE(key=0xF0, value=Op.GASPRICE)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x33f368f0b54063613cf5944941e8e0e4eeb64697"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=0x3D090,
                    address=0x33F368F0B54063613CF5944941E8E0E4EEB64697,
                    value=0x2,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xc3e151e887921d1edb46aae9b4a3ffc5b85e2a89"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALL 350000 <contract:0x1000000000000000000000000000000000000001> 1 0 64 0 64 ) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x55730,
                    address=0xC3E151E887921D1EDB46AAE9B4A3FFC5B85E2A89,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xeb09ff15547417853f6f4b240b8804769c37b0f1"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=3000000,
    )

    post = {
        callee: Account(
            storage={
                2: 1,
                4: 0xC3E151E887921D1EDB46AAE9B4A3FFC5B85E2A89,
                7: 2,
                230: 0x33F368F0B54063613CF5944941E8E0E4EEB64697,
                232: 0xEBAF50DEBF10E08302FE4280C32DF010463CA297,
                236: 64,
                238: 34,
                240: 10,
            },
        ),
        callee_1: Account(storage={1: 1}),
        contract: Account(storage={0: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
