"""
Test_revert_precompiled_touch_paris.

Ported from:
state_tests/stRevertTest/RevertPrecompiledTouch_ParisFiller.json
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
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertPrecompiledTouch_ParisFiller.json"],
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
def test_revert_precompiled_touch_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_revert_precompiled_touch_paris."""
    coinbase = Address(0x68795C4AA09D6F4ED3E5DEDDF8C2AD3049A601DA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000, nonce=1)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4012015,
    )

    addr_5 = pre.fund_eoa(amount=1)
    addr_6 = pre.fund_eoa(amount=1)
    addr_7 = pre.fund_eoa(amount=1)
    addr_8 = pre.fund_eoa(amount=1)
    addr_9 = pre.fund_eoa(amount=1)
    addr_10 = pre.fund_eoa(amount=1)
    addr_11 = pre.fund_eoa(amount=1)
    addr_12 = pre.fund_eoa(amount=1)
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
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_5: Account(nonce=0),
                addr_6: Account(nonce=0),
                addr_7: Account(nonce=0),
                addr_8: Account(nonce=0),
                addr_9: Account(nonce=0),
                addr_10: Account(nonce=0),
                addr_11: Account(nonce=0),
                addr_12: Account(nonce=0),
            },
        },
        {
            "indexes": {"data": [1, 2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_5: Account(nonce=0),
                addr_6: Account(nonce=0),
                addr_7: Account(nonce=0),
                addr_8: Account(nonce=0),
                addr_9: Account(nonce=0),
                addr_10: Account(nonce=0),
                addr_11: Account(nonce=0),
                addr_12: Account(nonce=0),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

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
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
