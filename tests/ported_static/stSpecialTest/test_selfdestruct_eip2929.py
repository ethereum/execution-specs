"""
Martin: @tkstanczak requested a state-test regarding selfdestructs in...

Ported from:
state_tests/stSpecialTest/selfdestructEIP2929Filler.json
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
    ["state_tests/stSpecialTest/selfdestructEIP2929Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_selfdestruct_eip2929(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Martin: @tkstanczak requested a state-test regarding selfdestructs..."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    addr_0x00000000000000000000000000000000000000aa = Address(
        "0x9ecbdbdbd8448cdd955755cdd81d6918e436f68a"
    )
    addr_0x00000000000000000000000000000000000000cc = Address(
        "0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3"
    )
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10944489199640098,
    )

    pre[addr_0x00000000000000000000000000000000000000aa] = Account(
        balance=0, nonce=1
    )
    pre[addr_0x00000000000000000000000000000000000000cc] = Account(
        balance=0, nonce=1
    )
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
        address=Address("0xb686be1a7a0f441fae9583884043ac034fe82089"),  # noqa: E501
    )
    # Source: raw
    # 0x60003574ffffffffffffffffffffffffffffffffffffffffff16ff
    addr_0x000000000000000000000000000000000000dead = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=Op.AND(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                Op.CALLDATALOAD(offset=0x0),
            )
        ),
        balance=1,
        nonce=1,
        address=Address("0xd2e5c26a2f035a63d0859e255621ed1e57148085"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=b"",
        gas_limit=8000000,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
