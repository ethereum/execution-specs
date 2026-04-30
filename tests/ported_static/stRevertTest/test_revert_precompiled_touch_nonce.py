"""
Test_revert_precompiled_touch_nonce.

Ported from:
state_tests/stRevertTest/RevertPrecompiledTouch_nonceFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertPrecompiledTouch_nonceFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_precompiled_touch_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_revert_precompiled_touch_nonce."""
    coinbase = Address(0x68795C4AA09D6F4ED3E5DEDDF8C2AD3049A601DA)
    addr_5 = Address(0x0000000000000000000000000000000000000001)
    addr_6 = Address(0x0000000000000000000000000000000000000002)
    addr_7 = Address(0x0000000000000000000000000000000000000003)
    addr_8 = Address(0x0000000000000000000000000000000000000004)
    addr_9 = Address(0x0000000000000000000000000000000000000005)
    addr_10 = Address(0x0000000000000000000000000000000000000006)
    addr_11 = Address(0x0000000000000000000000000000000000000007)
    addr_12 = Address(0x0000000000000000000000000000000000000008)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000, nonce=1)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4012015,
    )

    pre[addr_5] = Account(balance=0, nonce=1)
    pre[addr_6] = Account(balance=0, nonce=1)
    pre[addr_7] = Account(balance=0, nonce=1)
    pre[addr_8] = Account(balance=0, nonce=1)
    pre[addr_9] = Account(balance=0, nonce=1)
    pre[addr_10] = Account(balance=0, nonce=1)
    pre[addr_11] = Account(balance=0, nonce=1)
    pre[addr_12] = Account(balance=0, nonce=1)
    # Source: lll
    # {  (CALLCODE (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=Op.GAS,
            address=Op.CALLDATALOAD(offset=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xE7C596DE24CCC387DAA5C017066AEB25EA8D2F3F),  # noqa: E501
    )
    # Source: lll
    # { (CALL 50000 1 0 0 0 0 0) (CALL 50000 2 0 0 0 0 0) (CALL 50000 3 0 0 0 0 0) (CALL 50000 4 0 0 0 0 0) (CALL 50000 5 0 0 0 0 0) (CALL 50000 6 0 0 0 0 0) (CALL 50000 7 0 0 0 0 0) (CALL 50000 8 0 0 0 0 0) [[1]] (GAS) [[2]] (GAS) [[3]] (GAS) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0xC350,
                address=0x1,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0xC350,
                address=0x2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0xC350,
                address=0x3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0xC350,
                address=0x4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0xC350,
                address=0x5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0xC350,
                address=0x6,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0xC350,
                address=0x7,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0xC350,
                address=0x8,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.GAS)
        + Op.SSTORE(key=0x2, value=Op.GAS)
        + Op.SSTORE(key=0x3, value=Op.GAS)
        + Op.STOP,
        nonce=0,
        address=Address(0x87AAEB9E422487283B0B008EF445E32ACB9DD1AE),  # noqa: E501
    )
    # Source: lll
    # { (DELEGATECALL 50000 1 0 0 0 0) (DELEGATECALL 50000 2 0 0 0 0) (DELEGATECALL 50000 3 0 0 0 0) (DELEGATECALL 50000 4 0 0 0 0) (DELEGATECALL 50000 5 0 0 0 0) (DELEGATECALL 50000 6 0 0 0 0) (DELEGATECALL 50000 7 0 0 0 0) (DELEGATECALL 50000 8 0 0 0 0) [[1]] (GAS) [[2]] (GAS) [[3]] (GAS) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.DELEGATECALL(
                gas=0xC350,
                address=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0xC350,
                address=0x2,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0xC350,
                address=0x3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0xC350,
                address=0x4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0xC350,
                address=0x5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0xC350,
                address=0x6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0xC350,
                address=0x7,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0xC350,
                address=0x8,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.GAS)
        + Op.SSTORE(key=0x2, value=Op.GAS)
        + Op.SSTORE(key=0x3, value=Op.GAS)
        + Op.STOP,
        nonce=0,
        address=Address(0x31F52A66CF9D94C60F089A2CA9C4E784261C57FA),  # noqa: E501
    )
    # Source: lll
    # { (CALLCODE 50000 1 0 0 0 0 0) (CALLCODE 50000 2 0 0 0 0 0) (CALLCODE 50000 3 0 0 0 0 0) (CALLCODE 50000 4 0 0 0 0 0) (CALLCODE 50000 5 0 0 0 0 0) (CALLCODE 50000 6 0 0 0 0 0) (CALLCODE 50000 7 0 0 0 0 0) (CALLCODE 50000 8 0 0 0 0 0) [[1]] (GAS) [[2]] (GAS) [[3]] (GAS) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALLCODE(
                gas=0xC350,
                address=0x1,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0xC350,
                address=0x2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0xC350,
                address=0x3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0xC350,
                address=0x4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0xC350,
                address=0x5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0xC350,
                address=0x6,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0xC350,
                address=0x7,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0xC350,
                address=0x8,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.GAS)
        + Op.SSTORE(key=0x2, value=Op.GAS)
        + Op.SSTORE(key=0x3, value=Op.GAS)
        + Op.STOP,
        nonce=0,
        address=Address(0xDE1200B7ECAEA2D15B57D0F331AD5ADE8E924255),  # noqa: E501
    )
    # Source: lll
    # { (STATICCALL 50000 1 0 0 0 0) (STATICCALL 50000 2 0 0 0 0) (STATICCALL 50000 3 0 0 0 0) (STATICCALL 50000 4 0 0 0 0) (STATICCALL 50000 5 0 0 0 0) (STATICCALL 50000 6 0 0 0 0) (STATICCALL 50000 7 0 0 0 0) (STATICCALL 50000 8 0 0 0 0) [[1]] (GAS) [[2]] (GAS) [[3]] (GAS) }  # noqa: E501
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.STATICCALL(
                gas=0xC350,
                address=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0xC350,
                address=0x2,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0xC350,
                address=0x3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0xC350,
                address=0x4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0xC350,
                address=0x5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0xC350,
                address=0x6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0xC350,
                address=0x7,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0xC350,
                address=0x8,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.GAS)
        + Op.SSTORE(key=0x2, value=Op.GAS)
        + Op.SSTORE(key=0x3, value=Op.GAS)
        + Op.STOP,
        nonce=0,
        address=Address(0x10EF6D6218ADA53728683CEC4D5160C8C72159BD),  # noqa: E501
    )

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_2, left_padding=True),
        Hash(addr_3, left_padding=True),
        Hash(addr_4, left_padding=True),
    ]
    tx_gas = [100000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
    )

    post = {
        addr_5: Account(balance=0, nonce=1),
        addr_6: Account(balance=0, nonce=1),
        addr_7: Account(balance=0, nonce=1),
        addr_8: Account(balance=0, nonce=1),
        addr_9: Account(balance=0, nonce=1),
        addr_10: Account(balance=0, nonce=1),
        addr_11: Account(balance=0, nonce=1),
        addr_12: Account(balance=0, nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
