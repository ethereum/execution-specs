"""
call with value. call takes more gas then tx has, and more value than...

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest
callWithHighValueAndOOGatTxLevelFiller.json
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

TX_GAS = [3000000]

TX_VALUE = [0, 1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCallCreateCallCodeTest/callWithHighValueAndOOGatTxLevelFiller.json",  # noqa: E501
    ],
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
def test_call_with_high_value_and_oo_gat_tx_level(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Call with value. call takes more gas then tx has, and more value..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: raw bytecode
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x1)
            + Op.MSTORE8(offset=0x0, value=0x37)
            + Op.RETURN(offset=0x0, size=0x2)
        ),
        balance=23,
        nonce=0,
        address=Address("0x0896f13e800125c0ccec44f3c434335f0a97bc1b"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALL 3000001 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 100001 0 0 0 0 ) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x2DC6C1,
                    address=0x896F13E800125C0CCEC44F3C434335F0A97BC1B,
                    value=0x186A1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        storage={0x0: 0x5},
        balance=0x186A0,
        nonce=0,
        address=Address("0x9001fa64dbba07e3eb711a42cf25b34ccee2bd2b"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("6001600155603760005360026000f3")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000620186a1730896f13e800125c0ccec44f3c434335f0a97bc1b622dc6c1f160005500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={1: 1},
                    code=bytes.fromhex("6001600155603760005360026000f3"),
                ),
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "6000600060006000620186a1730896f13e800125c0ccec44f3c434335f0a97bc1b622dc6c1f160005500"  # noqa: E501
                    ),
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
