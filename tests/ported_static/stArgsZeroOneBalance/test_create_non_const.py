"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stArgsZeroOneBalance/createNonConstFiller.yml
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

TX_GAS = [400000]

TX_VALUE = [0, 1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stArgsZeroOneBalance/createNonConstFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 1, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_non_const(
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
        gas_limit=1000000,
    )

    # Source: LLL
    # { [[ 0 ]] (CREATE (BALANCE 0x095e7baea6a6c7c4c2dfeb977efac326af552d87) (BALANCE 0x095e7baea6a6c7c4c2dfeb977efac326af552d87) (BALANCE 0x095e7baea6a6c7c4c2dfeb977efac326af552d87)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CREATE(
                    value=Op.BALANCE(
                        address=0x95E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87,
                    ),
                    offset=Op.BALANCE(
                        address=0x95E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87,
                    ),
                    size=Op.BALANCE(
                        address=0x95E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87,
                    ),
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 0xD2571607E241ECF590ED94B12D87C94BABE36DB6},
                    code=bytes.fromhex(
                        "73095e7baea6a6c7c4c2dfeb977efac326af552d873173095e7baea6a6c7c4c2dfeb977efac326af552d873173095e7baea6a6c7c4c2dfeb977efac326af552d8731f060005500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 0xD2571607E241ECF590ED94B12D87C94BABE36DB6},
                    code=bytes.fromhex(
                        "73095e7baea6a6c7c4c2dfeb977efac326af552d873173095e7baea6a6c7c4c2dfeb977efac326af552d873173095e7baea6a6c7c4c2dfeb977efac326af552d8731f060005500"  # noqa: E501
                    ),
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
