"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stCreate2/CREATE2_Bounds3Filler.json
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
    "",
]

TX_GAS = [150000, 1000000, 16777216]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stCreate2/CREATE2_Bounds3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 1, 0, id="case1"),
        pytest.param(2, 2, 0, id="case2"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2_bounds3(
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
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
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
    # {  (MSTORE 0 0x6001600155601080600c6000396000f3006000355415600957005b6020356000 )  (MSTORE8 32 0x35) (MSTORE8 33 0x55) (CREATE2 1 0 0xffffffffffffffff 0) (CREATE2 1 0 0xffffffffffffffffffffffffffffffff 0) (CREATE2 1 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0) (CREATE2 1 0xfffffff 0 0) (CREATE2 1 0xffffffff 0 0) (CREATE2 1 0xffffffffffffffff 0 0) (CREATE2 1 0xffffffffffffffffffffffffffffffff 0 0) (CREATE2 1 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0 0) (CREATE2 1 0xfffffff 0xfffffff 0) (CREATE2 1 0xffffffff 0xffffffff 0) (CREATE2 1 0xffffffffffffffff 0xffffffffffffffff 0) (CREATE2 1 0xffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffff 0) (CREATE2 1 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0)}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x6001600155601080600C6000396000F3006000355415600957005B6020356000,  # noqa: E501
            )
            + Op.MSTORE8(offset=0x20, value=0x35)
            + Op.MSTORE8(offset=0x21, value=0x55)
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0x0,
                    size=0xFFFFFFFFFFFFFFFF,
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0x0,
                    size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0x0,
                    size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(value=0x1, offset=0xFFFFFFF, size=0x0, salt=0x0)
            )
            + Op.POP(
                Op.CREATE2(value=0x1, offset=0xFFFFFFFF, size=0x0, salt=0x0)
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0xFFFFFFFFFFFFFFFF,
                    size=0x0,
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    size=0x0,
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    size=0x0,
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1, offset=0xFFFFFFF, size=0xFFFFFFF, salt=0x0
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0xFFFFFFFF,
                    size=0xFFFFFFFF,
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0xFFFFFFFFFFFFFFFF,
                    size=0xFFFFFFFFFFFFFFFF,
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    salt=0x0,
                ),
            )
            + Op.CREATE2(
                value=0x1,
                offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                salt=0x0,
            )
            + Op.STOP
        ),
        balance=100,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "7f6001600155601080600c6000396000f3006000355415600957005b602035600060005260356020536055602153600067ffffffffffffffff60006001f55060006fffffffffffffffffffffffffffffffff60006001f55060007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60006001f55060006000630fffffff6001f5506000600063ffffffff6001f5506000600067ffffffffffffffff6001f550600060006fffffffffffffffffffffffffffffffff6001f550600060007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6001f5506000630fffffff630fffffff6001f550600063ffffffff63ffffffff6001f550600067ffffffffffffffff67ffffffffffffffff6001f55060006fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6001f55060007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6001f500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "7f6001600155601080600c6000396000f3006000355415600957005b602035600060005260356020536055602153600067ffffffffffffffff60006001f55060006fffffffffffffffffffffffffffffffff60006001f55060007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60006001f55060006000630fffffff6001f5506000600063ffffffff6001f5506000600067ffffffffffffffff6001f550600060006fffffffffffffffffffffffffffffffff6001f550600060007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6001f5506000630fffffff630fffffff6001f550600063ffffffff63ffffffff6001f550600067ffffffffffffffff67ffffffffffffffff6001f55060006fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6001f55060007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6001f500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "7f6001600155601080600c6000396000f3006000355415600957005b602035600060005260356020536055602153600067ffffffffffffffff60006001f55060006fffffffffffffffffffffffffffffffff60006001f55060007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60006001f55060006000630fffffff6001f5506000600063ffffffff6001f5506000600067ffffffffffffffff6001f550600060006fffffffffffffffffffffffffffffffff6001f550600060007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6001f5506000630fffffff630fffffff6001f550600063ffffffff63ffffffff6001f550600067ffffffffffffffff67ffffffffffffffff6001f55060006fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6001f55060007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6001f500"  # noqa: E501
                    )
                )
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
