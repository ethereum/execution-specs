"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/RevertSubCallStorageOOG2Filler.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "c0406226",
    "c0406226",
    "c0406226",
    "c0406226",
]

TX_GAS = [61500, 181000]

TX_VALUE = [0, 1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stRevertTest/RevertSubCallStorageOOG2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 1, id="case1"),
        pytest.param(2, 1, 0, id="case2"),
        pytest.param(3, 1, 1, id="case3"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_sub_call_storage_oog2(
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
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=bytes.fromhex(
            "60606040526000357c010000000000000000000000000000000000000000000000000000"  # noqa: E501
            "0000900463ffffffff168063b28175c4146046578063c0406226146052575b6000565b34"  # noqa: E501
            "60005760506076565b005b34600057605c6081565b604051808215151515815260200191"  # noqa: E501
            "505060405180910390f35b600c6000819055505b565b600060896076565b600d60008190"  # noqa: E501
            "5550600e6001819055505b905600a165627a7a72305820b7c6987c21e63fed8a74d89955"  # noqa: E501
            "7744a3be8d3fda191ce0f56cf261d6b860f6b40029"
        ),
        balance=1,
        nonce=0,
        address=Address("0x48bc00be37fe77bd0f7b7b8009f908fc534a028b"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "60606040526000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff168063b28175c4146046578063c0406226146052575b6000565b3460005760506076565b005b34600057605c6081565b604051808215151515815260200191505060405180910390f35b600c6000819055505b565b600060896076565b600d600081905550600e6001819055505b905600a165627a7a72305820b7c6987c21e63fed8a74d899557744a3be8d3fda191ce0f56cf261d6b860f6b40029"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "60606040526000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff168063b28175c4146046578063c0406226146052575b6000565b3460005760506076565b005b34600057605c6081565b604051808215151515815260200191505060405180910390f35b600c6000819055505b565b600060896076565b600d600081905550600e6001819055505b905600a165627a7a72305820b7c6987c21e63fed8a74d899557744a3be8d3fda191ce0f56cf261d6b860f6b40029"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 13, 1: 14},
                    code=bytes.fromhex(
                        "60606040526000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff168063b28175c4146046578063c0406226146052575b6000565b3460005760506076565b005b34600057605c6081565b604051808215151515815260200191505060405180910390f35b600c6000819055505b565b600060896076565b600d600081905550600e6001819055505b905600a165627a7a72305820b7c6987c21e63fed8a74d899557744a3be8d3fda191ce0f56cf261d6b860f6b40029"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 3, "gas": 1, "value": 1},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "60606040526000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff168063b28175c4146046578063c0406226146052575b6000565b3460005760506076565b005b34600057605c6081565b604051808215151515815260200191505060405180910390f35b600c6000819055505b565b600060896076565b600d600081905550600e6001819055505b905600a165627a7a72305820b7c6987c21e63fed8a74d899557744a3be8d3fda191ce0f56cf261d6b860f6b40029"  # noqa: E501
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
