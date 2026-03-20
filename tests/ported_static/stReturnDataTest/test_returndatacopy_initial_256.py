"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stReturnDataTest/returndatacopy_initial_256Filler.json
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
    "0000000000000000000000000000000000000000000000000000000000000064",
    "0000000000000000000000000000000000000000000000000000000000000063",
    "0000000000000000000000000000000000000000000000000000000000000065",
]

TX_GAS = [100000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stReturnDataTest/returndatacopy_initial_256Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(2, 0, 0, id="case2"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_initial_256(
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
        key=0x834185262E53584684BF2B72C64E510013C235D0F45E462DB65900455DF45A35
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    # Source: LLL
    # { (RETURNDATACOPY (- 0 (CALLDATALOAD 0)) 0 0x64) (MSTORE 0 0x112233445566778899aabbccddeeff) (SSTORE 0 (MLOAD 0)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.RETURNDATACOPY(
                dest_offset=Op.SUB(0x0, Op.CALLDATALOAD(offset=0x0)),
                offset=0x0,
                size=0x64,
            )
            + Op.MSTORE(offset=0x0, value=0x112233445566778899AABBCCDDEEFF)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x0: 0x1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x28f194b678152b435b5910dbdf69c091fa056347"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "606460006000356000033e6e112233445566778899aabbccddeeff60005260005160005500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "606460006000356000033e6e112233445566778899aabbccddeeff60005260005160005500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "606460006000356000033e6e112233445566778899aabbccddeeff60005260005160005500"  # noqa: E501
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
