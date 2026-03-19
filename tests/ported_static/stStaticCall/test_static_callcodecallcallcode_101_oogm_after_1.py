"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcodecallcallcode_101_OOGMAfter_1Filler.json
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
    "000000000000000000000000b9abd0ef44ae2df9f408d150c5b6fb6a181be9cf",
    "0000000000000000000000006486b0cd8779006e5cd706484b0d890b9a220805",
]

TX_GAS = [1720000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfter_1Filler.json",  # noqa: E501
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
def test_static_callcodecallcallcode_101_oogm_after_1(
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
        gas_limit=10000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0x61AD0,
                    address=0x677DB155FAB75972F19732AFB328A0EA6472A6AB,
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
        address=Address("0x18dc408f6983f318529a93583ee12f590c537820"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x335c5531b84765a7626e6e76688f18b81be5259c"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALLCODE(
                    gas=0xAAEF6,
                    address=0x18DC408F6983F318529A93583EE12F590C537820,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x3, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x6486b0cd8779006e5cd706484b0d890b9a220805"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALLCODE(
                    gas=0x1D4D4,
                    address=0xB126C622075B1189FB6C45E851641CFADDF65B36,
                    value=0x0,
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
        address=Address("0x677db155fab75972f19732afb328a0ea6472a6ab"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALLCODE(
                    gas=0x1D4D4,
                    address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                    value=0x0,
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
        address=Address("0x858db7418c9e1c32811e5bc39366bdf6e2ed2492"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALLCODE (GAS) (CALLDATALOAD 0) 0 0 0 0 0) [[ 1 ]] 1 }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=Op.GAS,
                    address=Op.CALLDATALOAD(offset=0x0),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xaab59f13d96113334fab5c68e4e62b61f6cbf647"),  # noqa: E501
    )
    callee_5 = pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xb126c622075b1189fb6c45e851641cfaddf65b36"),  # noqa: E501
    )
    callee_6 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALLCODE(
                    gas=0xAAEF6,
                    address=0xF4645C150A8060778AD94DFFE302081FC222DEDB,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x3, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xb9abd0ef44ae2df9f408d150c5b6fb6a181be9cf"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    callee_7 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0x61AD0,
                    address=0x858DB7418C9E1C32811E5BC39366BDF6E2ED2492,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x3F,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.POP(Op.EXTCODESIZE(address=0x1))
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x23)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xf4645c150a8060778ad94dffe302081fc222dedb"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "604060006040600073677db155fab75972f19732afb328a0ea6472a6ab62061ad0fa50600160035200"  # noqa: E501
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160035200")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "604060006040600060007318dc408f6983f318529a93583ee12f590c537820620aaef6f250600160035200"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6040600060406000600073b126c622075b1189fb6c45e851641cfaddf65b366201d4d4f250600160035200"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6040600060406000600073335c5531b84765a7626e6e76688f18b81be5259c6201d4d4f250600160035200"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "600060006000600060006000355af2600055600160015500"
                    ),
                ),
                callee_5: Account(code=bytes.fromhex("600160035500")),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6040600060406000600073f4645c150a8060778ad94dffe302081fc222dedb620aaef6f250600160035200"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "604060006040600073858db7418c9e1c32811e5bc39366bdf6e2ed249262061ad0fa505b61c3506080511015603f5760013b506001608051016080526023565b00"  # noqa: E501
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
                        "604060006040600073677db155fab75972f19732afb328a0ea6472a6ab62061ad0fa50600160035200"  # noqa: E501
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160035200")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "604060006040600060007318dc408f6983f318529a93583ee12f590c537820620aaef6f250600160035200"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6040600060406000600073b126c622075b1189fb6c45e851641cfaddf65b366201d4d4f250600160035200"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6040600060406000600073335c5531b84765a7626e6e76688f18b81be5259c6201d4d4f250600160035200"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "600060006000600060006000355af2600055600160015500"
                    ),
                ),
                callee_5: Account(code=bytes.fromhex("600160035500")),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6040600060406000600073f4645c150a8060778ad94dffe302081fc222dedb620aaef6f250600160035200"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "604060006040600073858db7418c9e1c32811e5bc39366bdf6e2ed249262061ad0fa505b61c3506080511015603f5760013b506001608051016080526023565b00"  # noqa: E501
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
