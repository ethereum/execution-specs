"""
Check balance in blackbox, just fill the balance consumed.

Ported from:
tests/static/state_tests/stStaticCall/static_CheckCallCostOOGFiller.json
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

TX_GAS = [22000, 1000000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_CheckCallCostOOGFiller.json",  # noqa: E501
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
@pytest.mark.slow
def test_static_check_call_cost_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Check balance in blackbox, just fill the balance consumed."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x3327048BBC0B8C348A6352BE62994144E64B8FF2CEC68D9FF4CA4E911ECD5D22
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0x5AF3107A4000)
    # Source: LLL
    # { (STATICCALL 100 <contract:0x2000000000000000000000000000000000000000> 0 0 0 0) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0x64,
                address=0xEBE7ED7A6E995C9843A6DF04E332981EBB2772E0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb59292b3a630476adbc4a3643c0815b682a5009a"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=0x1)
            + Op.SHA3(offset=0x0, size=0x2FFFFF)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xebe7ed7a6e995c9843a6df04e332981ebb2772e0"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600073ebe7ed7a6e995c9843a6df04e332981ebb2772e06064fa00"  # noqa: E501
                    )
                ),
                callee: Account(
                    code=bytes.fromhex("6001600152622fffff60002000")
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600073ebe7ed7a6e995c9843a6df04e332981ebb2772e06064fa00"  # noqa: E501
                    )
                ),
                callee: Account(
                    code=bytes.fromhex("6001600152622fffff60002000")
                ),
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
