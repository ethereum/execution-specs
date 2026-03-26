"""
test_call_ecrecover_overflow

Ported from:
state_tests/stPreCompiledContracts2/CallEcrecover_OverflowFiller.yml
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
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "917694f918c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c000000000000000000000000000000000000000000000000000000000000001cfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd03641411fffd310ac743f371de3b9f7f9cb56c0b28ad43601b4ab949f53faa07bd2c804",
    "917694f918c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c000000000000000000000000000000000000000000000000000000000000001cfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd03641421fffd310ac743f371de3b9f7f9cb56c0b28ad43601b4ab949f53faa07bd2c804",
    "917694f918c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c000000000000000000000000000000000000000000000000000000000000001cfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364140efffd310ac743f371de3b9f7f9cb56c0b28ad43601b4ab949f53faa07bd2c804",
    "917694f918c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c000000000000000000000000000000000000000000000000000000000000001cfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd036413fefffd310ac743f371de3b9f7f9cb56c0b28ad43601b4ab949f53faa07bd2c804",
    "917694f918c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c000000000000000000000000000000000000000000000000000000000000001c48b55bfa915ac795c431978d8a6a992b628d557da5ff759b307d495a36649353fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141",
    "917694f918c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c000000000000000000000000000000000000000000000000000000000000001c48b55bfa915ac795c431978d8a6a992b628d557da5ff759b307d495a36649353fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364142",
    "917694f918c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c000000000000000000000000000000000000000000000000000000000000001c48b55bfa915ac795c431978d8a6a992b628d557da5ff759b307d495a36649353fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364140",
    "917694f918c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c000000000000000000000000000000000000000000000000000000000000001c48b55bfa915ac795c431978d8a6a992b628d557da5ff759b307d495a36649353fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd036413f",
]
TX_GAS = [100000]
TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stPreCompiledContracts2/CallEcrecover_OverflowFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="fail",
        ),
        pytest.param(
            1, 0, 0,
            id="fail",
        ),
        pytest.param(
            2, 0, 0,
            id="fail",
        ),
        pytest.param(
            3, 0, 0,
            id="pass01",
        ),
        pytest.param(
            4, 0, 0,
            id="fail",
        ),
        pytest.param(
            5, 0, 0,
            id="fail",
        ),
        pytest.param(
            6, 0, 0,
            id="pass02",
        ),
        pytest.param(
            7, 0, 0,
            id="pass03",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_call_ecrecover_overflow(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_call_ecrecover_overflow"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    # Source: yul
    # berlin
    # {
    #  // Copy Hash, V, R, S values
    #  calldatacopy(0x00, 0x04, 0x80)
    # 
    #  // Call the EC Recover Precompile
    #  sstore(0, call(3000, 1, 0, 0, 0x80, 0x80, 0x20))
    #  sstore(1, mload(0x80))
    # }
    target = pre.deploy_contract(
        code=Op.CALLDATACOPY(dest_offset=0x0, offset=0x4, size=0x80)
        + Op.SSTORE(key=0x0, value=Op.CALL(gas=0xbb8, address=0x1, value=Op.DUP1, args_offset=0x0, args_size=Op.DUP1, ret_offset=0x80, ret_size=0x20))  # noqa: E501
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80)) + Op.STOP,
        nonce=0,
        address=Address("0xdb8963071feae3b63e19d9d7af8ee89a92e99356"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 1, 2, 4, 5], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(storage={0: 1, 1: 0})},
        },
        {
            "indexes": {'data': [3], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 1,
            1: 0x2182da748249a933bf737586b80212df19b8f829,
        },
            ),
    },
        },
        {
            "indexes": {'data': [6], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 1,
            1: 0x1b85ac3c9b09de43659c5d04a2d9c75457d9abf4,
        },
            ),
    },
        },
        {
            "indexes": {'data': [7], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 1,
            1: 0xd0277c8a3eccd462a313fc60161bac36b16e8699,
        },
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
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
