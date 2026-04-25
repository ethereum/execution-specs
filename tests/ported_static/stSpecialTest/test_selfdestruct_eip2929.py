"""
Martin: @tkstanczak requested a state-test regarding selfdestructs in...

Ported from:
state_tests/stSpecialTest/selfdestructEIP2929Filler.json
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
    ["state_tests/stSpecialTest/selfdestructEIP2929Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_selfdestruct_eip2929(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Martin: @tkstanczak requested a state-test regarding selfdestructs..."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10944489199640098,
    )

    addr = pre.fund_eoa(amount=0)  # noqa: F841
    addr_2 = pre.fund_eoa(amount=0)  # noqa: F841
    # Source: raw
    # 0x6000600060006000600060cc6000f1506000600060006000600060dd6000f1506000600060006000600060036000f15060aa6000526000600060206000600061dead5af15060aa6000526000600060206000600061dead5af15060bb6000526000600060206000600061dead5af15060bb6000526000600060206000600061dead5af15060cc6000526000600060206000600061dead5af15060cc6000526000600060206000600061dead5af15060dd6000526000600060206000600061dead5af15060dd6000526000600060206000600061dead5af15060016000526000600060206000600061dead5af15060016000526000600060206000600061dead5af15060026000526000600060206000600061dead5af15060026000526000600060206000600061dead5af15060036000526000600060206000600061dead5af1506001600155  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x0,
                address=0xCC,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x0,
                address=0xDD,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x0,
                address=0x3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0xAA)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0xAA)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0xBB)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0xBB)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0xCC)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0xCC)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0xDD)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0xDD)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0x1)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0x1)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0x2)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0x2)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0x3)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=0x1),
        balance=1,
        nonce=1,
    )
    # Source: raw
    # 0x60003574ffffffffffffffffffffffffffffffffffffffffff16ff
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=Op.AND(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                Op.CALLDATALOAD(offset=0x0),
            )
        ),
        balance=1,
        nonce=1,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=8000000,
    )

    post = {target: Account(storage={1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
