"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcallcodecallcode_011_2Filler.json
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
    "000000000000000000000000709eb538153d5f98f0b8482c462070c26db1cbae",
    "0000000000000000000000003cea889fd03a922cc673d25e5db4e72743aa4878",
]

TX_GAS = [3000000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcallcodecallcode_011_2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_callcallcodecallcode_011_2(
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

    # Source: LLL
    # {  (MSTORE 0 (CALLDATALOAD 0)) [[ 0 ]] (STATICCALL 350000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
            + Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x55730,
                    address=0x21A2D07156B4F874F3B25DFD175145C9CCEC1E19,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x023ae6338fbe9709a6449bfb0821f5aa83987b26"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=0x493E0,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x21a2d07156b4f874f3b25dfd175145c9ccec1e19"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x2a142c79a9b097c111ce945214226126b75e332c"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=0x3D090,
                address=0x2A142C79A9B097C111CE945214226126B75E332C,
                value=0x1,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x3cea889fd03a922cc673d25e5db4e72743aa4878"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=0x3D090,
                address=0x2A142C79A9B097C111CE945214226126B75E332C,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x709eb538153d5f98f0b8482c462070c26db1cbae"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "60003560005260406000604060007321a2d07156b4f874f3b25dfd175145c9ccec1e1962055730fa600055600160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "60406000604060006000600035620493e0f200"
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160015200")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60406000604060006001732a142c79a9b097c111ce945214226126b75e332c6203d090f200"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "60406000604060006000732a142c79a9b097c111ce945214226126b75e332c6203d090f200"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "60003560005260406000604060007321a2d07156b4f874f3b25dfd175145c9ccec1e1962055730fa600055600160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "60406000604060006000600035620493e0f200"
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160015200")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60406000604060006001732a142c79a9b097c111ce945214226126b75e332c6203d090f200"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "60406000604060006000732a142c79a9b097c111ce945214226126b75e332c6203d090f200"  # noqa: E501
                    )
                ),
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
