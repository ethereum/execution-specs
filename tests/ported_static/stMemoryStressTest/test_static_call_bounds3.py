"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemoryStressTest/static_CALL_Bounds3Filler.json
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
    [
        "tests/static/state_tests/stMemoryStressTest/static_CALL_Bounds3Filler.json",  # noqa: E501
    ],
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
def test_static_call_bounds3(
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
        key=0xEF111BBDAB3A1622936AFDFC9BBEC4B5BC05B4FA4B1EF0CE2A55CEF552F7650E
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
    )
    # Source: LLL
    # { (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffff 0 0xffffffffffffffff)  (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffff)  (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffff 0xffffffff 0xffffffff 0xffffffff) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffff 0xffffffffffffffff 0xffffffffffffffff 0xffffffffffffffff) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffff) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0xCC704D60C46B9C08AAB4D15281184441AC7ED35C,
                    args_offset=0x0,
                    args_size=0xFFFFFFFFFFFFFFFF,
                    ret_offset=0x0,
                    ret_size=0xFFFFFFFFFFFFFFFF,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0xCC704D60C46B9C08AAB4D15281184441AC7ED35C,
                    args_offset=0x0,
                    args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    ret_offset=0x0,
                    ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0xCC704D60C46B9C08AAB4D15281184441AC7ED35C,
                    args_offset=0x0,
                    args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    ret_offset=0x0,
                    ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0xCC704D60C46B9C08AAB4D15281184441AC7ED35C,
                    args_offset=0xFFFFFFFF,
                    args_size=0xFFFFFFFF,
                    ret_offset=0xFFFFFFFF,
                    ret_size=0xFFFFFFFF,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0xCC704D60C46B9C08AAB4D15281184441AC7ED35C,
                    args_offset=0xFFFFFFFFFFFFFFFF,
                    args_size=0xFFFFFFFFFFFFFFFF,
                    ret_offset=0xFFFFFFFFFFFFFFFF,
                    ret_size=0xFFFFFFFFFFFFFFFF,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0xCC704D60C46B9C08AAB4D15281184441AC7ED35C,
                    args_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    ret_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ),
            )
            + Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=0xCC704D60C46B9C08AAB4D15281184441AC7ED35C,
                args_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ret_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x83143406093d1f3560dd269416596d3406f1c991"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xcc704d60c46b9c08aab4d15281184441ac7ed35c"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "67ffffffffffffffff600067ffffffffffffffff600073cc704d60c46b9c08aab4d15281184441ac7ed35c6707fffffffffffffffa506fffffffffffffffffffffffffffffffff60006fffffffffffffffffffffffffffffffff600073cc704d60c46b9c08aab4d15281184441ac7ed35c6707fffffffffffffffa507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff600073cc704d60c46b9c08aab4d15281184441ac7ed35c6707fffffffffffffffa5063ffffffff63ffffffff63ffffffff63ffffffff73cc704d60c46b9c08aab4d15281184441ac7ed35c6707fffffffffffffffa5067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff73cc704d60c46b9c08aab4d15281184441ac7ed35c6707fffffffffffffffa506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff73cc704d60c46b9c08aab4d15281184441ac7ed35c6707fffffffffffffffa507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff73cc704d60c46b9c08aab4d15281184441ac7ed35c6707fffffffffffffffa00"  # noqa: E501
                    )
                ),
                callee: Account(code=bytes.fromhex("60005460010160005200")),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "67ffffffffffffffff600067ffffffffffffffff600073cc704d60c46b9c08aab4d15281184441ac7ed35c6707fffffffffffffffa506fffffffffffffffffffffffffffffffff60006fffffffffffffffffffffffffffffffff600073cc704d60c46b9c08aab4d15281184441ac7ed35c6707fffffffffffffffa507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff600073cc704d60c46b9c08aab4d15281184441ac7ed35c6707fffffffffffffffa5063ffffffff63ffffffff63ffffffff63ffffffff73cc704d60c46b9c08aab4d15281184441ac7ed35c6707fffffffffffffffa5067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff73cc704d60c46b9c08aab4d15281184441ac7ed35c6707fffffffffffffffa506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff73cc704d60c46b9c08aab4d15281184441ac7ed35c6707fffffffffffffffa507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff73cc704d60c46b9c08aab4d15281184441ac7ed35c6707fffffffffffffffa00"  # noqa: E501
                    )
                ),
                callee: Account(code=bytes.fromhex("60005460010160005200")),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
