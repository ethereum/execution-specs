"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemoryStressTest/CALLCODE_BoundsFiller.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "",
    "",
]

TX_GAS = [150000, 16777216]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stMemoryStressTest/CALLCODE_BoundsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 1, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_callcode_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x50EADFB1030587AB3A993A6ECC073041FC3B45E119DAA31A13D78C7E209631A5
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: LLL
    # {  (CALLCODE 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0 0 0 0) (CALLCODE 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0 0xfffffff 0 0xfffffff) (CALLCODE 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0 0xffffffff 0 0xffffffff)  (CALLCODE 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xfffffff 0 0xfffffff 0) (CALLCODE 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffff 0 0xffffffff 0) (CALLCODE 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffff 0 0xffffffffffffffff 0) (CALLCODE 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffff 0) (CALLCODE 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0)  }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALLCODE(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0xFFFFFFF,
                    ret_offset=0x0,
                    ret_size=0xFFFFFFF,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0xFFFFFFFF,
                    ret_offset=0x0,
                    ret_size=0xFFFFFFFF,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    value=0x0,
                    args_offset=0xFFFFFFF,
                    args_size=0x0,
                    ret_offset=0xFFFFFFF,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    value=0x0,
                    args_offset=0xFFFFFFFF,
                    args_size=0x0,
                    ret_offset=0xFFFFFFFF,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    value=0x0,
                    args_offset=0xFFFFFFFFFFFFFFFF,
                    args_size=0x0,
                    ret_offset=0xFFFFFFFFFFFFFFFF,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    value=0x0,
                    args_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    args_size=0x0,
                    ret_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    ret_size=0x0,
                ),
            )
            + Op.CALLCODE(
                gas=0x7FFFFFFFFFFFFFF,
                address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                value=0x0,
                args_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                args_size=0x0,
                ret_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x3f4ed7c54cd8a44e2d6b4d967e8e070a8c4a4f34"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0))) + Op.STOP
        ),
        nonce=0,
        address=Address("0x849f53126ade5f72469029537296f2b6644d4d41"),  # noqa: E501
    )
    pre[sender] = Account(
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff250630fffffff6000630fffffff6000600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff25063ffffffff600063ffffffff6000600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff2506000630fffffff6000630fffffff600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff250600063ffffffff600063ffffffff600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff250600067ffffffffffffffff600067ffffffffffffffff600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff25060006fffffffffffffffffffffffffffffffff60006fffffffffffffffffffffffffffffffff600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff25060007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff200"  # noqa: E501
                    )
                ),
                callee: Account(code=bytes.fromhex("60005460010160005500")),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff250630fffffff6000630fffffff6000600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff25063ffffffff600063ffffffff6000600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff2506000630fffffff6000630fffffff600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff250600063ffffffff600063ffffffff600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff250600067ffffffffffffffff600067ffffffffffffffff600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff25060006fffffffffffffffffffffffffffffffff60006fffffffffffffffffffffffffffffffff600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff25060007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff600073849f53126ade5f72469029537296f2b6644d4d416707fffffffffffffff200"  # noqa: E501
                    )
                ),
                callee: Account(code=bytes.fromhex("60005460010160005500")),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
