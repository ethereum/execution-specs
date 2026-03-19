"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcallcodecallcode_011_OOGMAfter_2Filler.json
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
    "0000000000000000000000007da35806c36ef9661efa1128809b18a8ed9c78f0",
    "00000000000000000000000045445092b290295fb6c954103ff2ce24cf3cfaf5",
]

TX_GAS = [172000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMAfter_2Filler.json",  # noqa: E501
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
def test_static_callcallcodecallcode_011_oogm_after_2(
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
            Op.MSTORE(offset=0x3, value=0x1)
            + Op.POP(
                Op.CALLCODE(
                    gas=0x4E34,
                    address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x20, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1e28daa61ad32aac8383a1f7b17986c69f0c3273"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x335c5531b84765a7626e6e76688f18b81be5259c"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x3, value=0x1)
            + Op.POP(
                Op.CALLCODE(
                    gas=0x9C90,
                    address=0x1E28DAA61AD32AAC8383A1F7B17986C69F0C3273,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x45,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.POP(Op.EXTCODESIZE(address=0x1))
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x29)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x45445092b290295fb6c954103ff2ce24cf3cfaf5"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (STATICCALL 60150 (CALLDATALOAD 0) 0 64 0 64 ) [[ 1 ]] 1 }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0xEAF6,
                    address=Op.CALLDATALOAD(offset=0x0),
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
        address=Address("0x652a62e8338e91a46aa8387a2c205f35f79347ab"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x3, value=0x1)
            + Op.POP(
                Op.CALLCODE(
                    gas=0x9C90,
                    address=0x1E28DAA61AD32AAC8383A1F7B17986C69F0C3273,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x3, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x7da35806c36ef9661efa1128809b18a8ed9c78f0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "60016003526040600060406000600073335c5531b84765a7626e6e76688f18b81be5259c614e34f250600160205200"  # noqa: E501
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160035200")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "600160035260406000604060006000731e28daa61ad32aac8383a1f7b17986c69f0c3273619c90f2505b61c350608051101560455760013b506001608051016080526029565b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "604060006040600060003561eaf6fa600055600160015500"
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "600160035260406000604060006000731e28daa61ad32aac8383a1f7b17986c69f0c3273619c90f250600160035500"  # noqa: E501
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
                        "60016003526040600060406000600073335c5531b84765a7626e6e76688f18b81be5259c614e34f250600160205200"  # noqa: E501
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160035200")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "600160035260406000604060006000731e28daa61ad32aac8383a1f7b17986c69f0c3273619c90f2505b61c350608051101560455760013b506001608051016080526029565b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "604060006040600060003561eaf6fa600055600160015500"
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "600160035260406000604060006000731e28daa61ad32aac8383a1f7b17986c69f0c3273619c90f250600160035500"  # noqa: E501
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
