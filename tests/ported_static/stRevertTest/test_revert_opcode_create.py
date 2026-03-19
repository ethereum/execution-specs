"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/RevertOpcodeCreateFiller.json
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
    "600160005560016000fe6011600155",
    "600160005560016000fe6011600155",
]

TX_GAS = [460000, 70000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRevertTest/RevertOpcodeCreateFiller.json"],
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
def test_revert_opcode_create(
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

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: LLL
    # { (MSTORE 0 0x600160005560016000fd6011600155 ) [[1]](CREATE 1 17 15) [[0]] 12 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x600160005560016000FD6011600155)
            + Op.SSTORE(
                key=0x1, value=Op.CREATE(value=0x1, offset=0x11, size=0xF)
            )
            + Op.SSTORE(key=0x0, value=0xC)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 12},
                    code=bytes.fromhex(
                        "6e600160005560016000fd6011600155600052600f60116001f0600155600c60005500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "6e600160005560016000fd6011600155600052600f60116001f0600155600c60005500"  # noqa: E501
                    )
                )
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
