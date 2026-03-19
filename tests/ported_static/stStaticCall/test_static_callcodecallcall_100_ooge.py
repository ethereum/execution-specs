"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcodecallcall_100_OOGEFiller.json
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
    "000000000000000000000000b126c622075b1189fb6c45e851641cfaddf65b36",
    "000000000000000000000000fbef21c5a6c2adcf3d769f085e0cc9fe9a8df954",
]

TX_GAS = [172000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcodecallcall_100_OOGEFiller.json",  # noqa: E501
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
def test_static_callcodecallcall_100_ooge(
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

    callee = pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0x4E34,
                    address=Op.CALLDATALOAD(offset=0x20),
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x3, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x5ac4ee179abd5ea5f60962e651ded51161a55b6e"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xb126c622075b1189fb6c45e851641cfaddf65b36"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x0))
            + Op.POP(
                Op.STATICCALL(
                    gas=0x186A0,
                    address=0x5AC4EE179ABD5EA5F60962E651DED51161A55B6E,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x3, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xc4961fc5bdc17da68e909d07947a5e030952891e"),  # noqa: E501
    )
    # Source: LLL
    # {  (MSTORE 0 (CALLDATALOAD 0)) [[ 0 ]] (DELEGATECALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
            + Op.SSTORE(
                key=0x0,
                value=Op.DELEGATECALL(
                    gas=0x249F0,
                    address=0xC4961FC5BDC17DA68E909D07947A5E030952891E,
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
        address=Address("0xdcff1ef291ec7b6a606ac4284680db5a06f33054"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    callee_3 = pre.deploy_contract(
        code=(
            Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1C,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.POP(Op.EXTCODESIZE(address=0x1))
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x0)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xfbef21c5a6c2adcf3d769f085e0cc9fe9a8df954"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6040600060406000602035614e34fa50600160035200"
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160035500")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6000356020526040600060406000735ac4ee179abd5ea5f60962e651ded51161a55b6e620186a0fa50600160035200"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "600035600052604060006040600073c4961fc5bdc17da68e909d07947a5e030952891e620249f0f4600055600160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6040600060406000602035614e34fa50600160035200"
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160035500")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6000356020526040600060406000735ac4ee179abd5ea5f60962e651ded51161a55b6e620186a0fa50600160035200"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "600035600052604060006040600073c4961fc5bdc17da68e909d07947a5e030952891e620249f0f4600055600160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b00"  # noqa: E501
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
