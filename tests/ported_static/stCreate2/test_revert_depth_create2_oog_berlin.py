"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stCreate2/RevertDepthCreate2OOGBerlinFiller.json
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
    "000000000000000000000000000000000000000000000000000000000000ea60",
    "000000000000000000000000000000000000000000000000000000000001ea60",
]

TX_GAS = [110000, 170000]

TX_VALUE = [1, 0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCreate2/RevertDepthCreate2OOGBerlinFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(0, 0, 1, id="case1"),
        pytest.param(0, 1, 0, id="case2"),
        pytest.param(0, 1, 1, id="case3"),
        pytest.param(1, 0, 0, id="case4"),
        pytest.param(1, 0, 1, id="case5"),
        pytest.param(1, 1, 0, id="case6"),
        pytest.param(1, 1, 1, id="case7"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_depth_create2_oog_berlin(
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
        gas_limit=10000000,
    )

    # Source: LLL
    # { [[0]] 1 [[1]] (CALL (CALLDATALOAD 0) 0xb000000000000000000000000000000000000000 0 0 0 0 0) [[4]] 12 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=Op.CALLDATALOAD(offset=0x0),
                    address=0xB000000000000000000000000000000000000000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x4, value=0xC)
            + Op.STOP
        ),
        balance=5,
        nonce=54,
        address=Address("0xa000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: LLL
    # { [[2]] 8 (CREATE2 0 0 0 0) [[3]] 12}
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x2, value=0x8)
            + Op.POP(Op.CREATE2(value=0x0, offset=0x0, size=0x0, salt=0x0))
            + Op.SSTORE(key=0x3, value=0xC)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb000000000000000000000000000000000000000"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x05a28fc366483258507bcf739658573cb47e4fad"): Account(
                    nonce=1
                ),
                contract: Account(storage={0: 1, 1: 1, 4: 12}),
                callee: Account(storage={2: 8, 3: 12}),
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(
                    "0x05a28fc366483258507bcf739658573cb47e4fad"
                ): Account.NONEXISTENT,
                contract: Account(storage={0: 1, 4: 12}),
                callee: Account(storage={}),
            },
        },
        {
            "indexes": {"data": [1, 0], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(
                    "0x05a28fc366483258507bcf739658573cb47e4fad"
                ): Account.NONEXISTENT,
                contract: Account(storage={}),
                callee: Account(storage={}),
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
