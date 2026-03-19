"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcallcodecall_010_OOGEFiller.json
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
    "0000000000000000000000000d195fccf4102d8b6b6798768727ae0915c88ed7",
    "000000000000000000000000c45fe363c9ac4e1feed02b03a212fdf979a74505",
]

TX_GAS = [1720000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcallcodecall_010_OOGEFiller.json",  # noqa: E501
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
def test_static_callcallcodecall_010_ooge(
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
                    gas=0x1D4D4,
                    address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
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
        address=Address("0x0d195fccf4102d8b6b6798768727ae0915c88ed7"),  # noqa: E501
    )
    # Source: LLL
    # { (MSTORE 0 (CALLDATALOAD 0)) [[ 0 ]] (STATICCALL 500000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
            + Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x7A120,
                    address=0x39C3AAD8C9ECF3BE71828CAFFEEE06727FDA4679,
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
        address=Address("0x33344ff747b678f9e86028b0c745d8ab0e0d1792"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x335c5531b84765a7626e6e76688f18b81be5259c"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.DELEGATECALL(
                    gas=0x493E0,
                    address=Op.CALLDATALOAD(offset=0x0),
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x39c3aad8c9ecf3be71828caffeee06727fda4679"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0x1D4D4,
                    address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xc45fe363c9ac4e1feed02b03a212fdf979a74505"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "604060006040600073335c5531b84765a7626e6e76688f18b81be5259c6201d4d4fa505b61c3506080511015603f5760013b506001608051016080526023565b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "60003560005260406000604060007339c3aad8c9ecf3be71828caffeee06727fda46796207a120fa600055600160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(code=bytes.fromhex("600160035200")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6040600060406000600035620493e0f450600160015200"
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "604060006040600073335c5531b84765a7626e6e76688f18b81be5259c6201d4d4fa50600160015500"  # noqa: E501
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
                        "604060006040600073335c5531b84765a7626e6e76688f18b81be5259c6201d4d4fa505b61c3506080511015603f5760013b506001608051016080526023565b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "60003560005260406000604060007339c3aad8c9ecf3be71828caffeee06727fda46796207a120fa600055600160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(code=bytes.fromhex("600160035200")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6040600060406000600035620493e0f450600160015200"
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "604060006040600073335c5531b84765a7626e6e76688f18b81be5259c6201d4d4fa50600160015500"  # noqa: E501
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
