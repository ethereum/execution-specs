"""
Test_revert_depth_create_address_collision.

Ported from:
state_tests/stRevertTest/RevertDepthCreateAddressCollisionFiller.json
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
TX_GAS = [110000, 160000]
TX_VALUE = [1, 0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertDepthCreateAddressCollisionFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-g0-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="d0-g0-v1",
        ),
        pytest.param(
            0,
            1,
            0,
            id="d0-g1-v0",
        ),
        pytest.param(
            0,
            1,
            1,
            id="d0-g1-v1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-g0-v0",
        ),
        pytest.param(
            1,
            0,
            1,
            id="d1-g0-v1",
        ),
        pytest.param(
            1,
            1,
            0,
            id="d1-g1-v0",
        ),
        pytest.param(
            1,
            1,
            1,
            id="d1-g1-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_depth_create_address_collision(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_revert_depth_create_address_collision."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { [[0]] 1 [[1]] (CALL (CALLDATALOAD 0) <contract:0xb000000000000000000000000000000000000000> 0 0 0 0 0) [[4]] 12 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=Op.CALLDATALOAD(offset=0x0),
                address=0xB1B49241A4ECF7860872E686090781C906B1B437,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x4, value=0xC)
        + Op.STOP,
        balance=5,
        nonce=54,
        address=Address("0x97e33a176b7c8d61b356d1c170ac2119d28867df"),  # noqa: E501
    )
    # Source: lll
    # { [[2]] 8 (CREATE 0 0 0) [[3]] 12}
    addr_0xb000000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x2, value=0x8)
        + Op.POP(Op.CREATE(value=0x0, offset=0x0, size=0x0))
        + Op.SSTORE(key=0x3, value=0xC)
        + Op.STOP,
        nonce=0,
        address=Address("0xb1b49241a4ecf7860872e686090781c906b1b437"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={},
                    code=bytes.fromhex(
                        "60016000556000600060006000600073b1b49241a4ecf7860872e686090781c906b1b437600035f1600155600c60045500"  # noqa: E501
                    ),
                    nonce=54,
                ),
                addr_0xb000000000000000000000000000000000000000: Account(
                    storage={}
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={0: 1, 4: 12},
                    code=bytes.fromhex(
                        "60016000556000600060006000600073b1b49241a4ecf7860872e686090781c906b1b437600035f1600155600c60045500"  # noqa: E501
                    ),
                    nonce=54,
                ),
                addr_0xb000000000000000000000000000000000000000: Account(
                    storage={}
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={},
                    code=bytes.fromhex(
                        "60016000556000600060006000600073b1b49241a4ecf7860872e686090781c906b1b437600035f1600155600c60045500"  # noqa: E501
                    ),
                    balance=5,
                    nonce=54,
                ),
                addr_0xb000000000000000000000000000000000000000: Account(
                    storage={}
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={},
                    code=bytes.fromhex(
                        "60016000556000600060006000600073b1b49241a4ecf7860872e686090781c906b1b437600035f1600155600c60045500"  # noqa: E501
                    ),
                    nonce=54,
                ),
                addr_0xb000000000000000000000000000000000000000: Account(
                    storage={}
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
