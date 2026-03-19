"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stPreCompiledContracts2
CallEcrecover_OverflowFiller.yml
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
    "917694f918c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c000000000000000000000000000000000000000000000000000000000000001cfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd03641421fffd310ac743f371de3b9f7f9cb56c0b28ad43601b4ab949f53faa07bd2c804",  # noqa: E501
    "917694f918c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c000000000000000000000000000000000000000000000000000000000000001cfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364140efffd310ac743f371de3b9f7f9cb56c0b28ad43601b4ab949f53faa07bd2c804",  # noqa: E501
    "917694f918c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c000000000000000000000000000000000000000000000000000000000000001c48b55bfa915ac795c431978d8a6a992b628d557da5ff759b307d495a36649353fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141",  # noqa: E501
    "917694f918c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c000000000000000000000000000000000000000000000000000000000000001c48b55bfa915ac795c431978d8a6a992b628d557da5ff759b307d495a36649353fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364142",  # noqa: E501
    "",
    "917694f918c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c000000000000000000000000000000000000000000000000000000000000001cfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd03641411fffd310ac743f371de3b9f7f9cb56c0b28ad43601b4ab949f53faa07bd2c804",  # noqa: E501
    "917694f918c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c000000000000000000000000000000000000000000000000000000000000001c48b55bfa915ac795c431978d8a6a992b628d557da5ff759b307d495a36649353fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364140",  # noqa: E501
    "917694f918c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c000000000000000000000000000000000000000000000000000000000000001c48b55bfa915ac795c431978d8a6a992b628d557da5ff759b307d495a36649353fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd036413f",  # noqa: E501
]

TX_GAS = [100000]

TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stPreCompiledContracts2/CallEcrecover_OverflowFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(2, 0, 0, id="case2"),
        pytest.param(3, 0, 0, id="case3"),
        pytest.param(5, 0, 0, id="case4"),
        pytest.param(3, 0, 0, id="case5"),
        pytest.param(6, 0, 0, id="case6"),
        pytest.param(7, 0, 0, id="case7"),
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
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: Yul
    # {
    #  // Copy Hash, V, R, S values
    #  calldatacopy(0x00, 0x04, 0x80)
    #
    #  // Call the EC Recover Precompile
    #  sstore(0, call(3000, 1, 0, 0, 0x80, 0x80, 0x20))
    #  sstore(1, mload(0x80))
    # }
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATACOPY(dest_offset=0x0, offset=0x4, size=0x80)
            + Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0xBB8,
                    address=0x1,
                    value=Op.DUP1,
                    args_offset=0x0,
                    args_size=Op.DUP1,
                    ret_offset=0x80,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xdb8963071feae3b63e19d9d7af8ee89a92e99356"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "6080600460003760206080806000806001610bb8f160005560805160015500"  # noqa: E501
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
                        "6080600460003760206080806000806001610bb8f160005560805160015500"  # noqa: E501
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
                        "6080600460003760206080806000806001610bb8f160005560805160015500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "6080600460003760206080806000806001610bb8f160005560805160015500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "6080600460003760206080806000806001610bb8f160005560805160015500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 1,
                        1: 0x2182DA748249A933BF737586B80212DF19B8F829,
                    },
                    code=bytes.fromhex(
                        "6080600460003760206080806000806001610bb8f160005560805160015500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 1,
                        1: 0x1B85AC3C9B09DE43659C5D04A2D9C75457D9ABF4,
                    },
                    code=bytes.fromhex(
                        "6080600460003760206080806000806001610bb8f160005560805160015500"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 1,
                        1: 0xD0277C8A3ECCD462A313FC60161BAC36B16E8699,
                    },
                    code=bytes.fromhex(
                        "6080600460003760206080806000806001610bb8f160005560805160015500"  # noqa: E501
                    ),
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
