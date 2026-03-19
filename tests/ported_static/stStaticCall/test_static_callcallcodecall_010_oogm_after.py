"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcallcodecall_010_OOGMAfterFiller.json
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
    "000000000000000000000000c00fba9c86d497814a90912f8f6c63801ea59908",
    "0000000000000000000000003a2fb8850eea3cbd892bb77ff68da146ead9c49d",
]

TX_GAS = [1720000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcallcodecall_010_OOGMAfterFiller.json",  # noqa: E501
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
def test_static_callcallcodecall_010_oogm_after(
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
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x335c5531b84765a7626e6e76688f18b81be5259c"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.DELEGATECALL(
                    gas=0x61AD0,
                    address=0x5AD1F77E14FE15F07A2F5DF1480DCABA5B4B6435,
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
        address=Address("0x3a2fb8850eea3cbd892bb77ff68da146ead9c49d"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0x1D4E8,
                address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x5ad1f77e14fe15f07a2f5df1480dcaba5b4b6435"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.DELEGATECALL(
                    gas=0x61AD0,
                    address=0x5AD1F77E14FE15F07A2F5DF1480DCABA5B4B6435,
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
        address=Address("0xc00fba9c86d497814a90912f8f6c63801ea59908"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: LLL
    # {  [[ 0 ]] (STATICCALL 600150 (CALLDATALOAD 0) 0 64 0 64 ) [[ 1 ]] 1 }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x92856,
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
        address=Address("0xf1f083974fd68b961e68130c27fc5ef37b49c1df"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600160035200")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6040600060406000735ad1f77e14fe15f07a2f5df1480dcaba5b4b643562061ad0f4505b61c3506080511015603f5760013b506001608051016080526023565b00"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "604060006040600073335c5531b84765a7626e6e76688f18b81be5259c6201d4e8fa00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6040600060406000735ad1f77e14fe15f07a2f5df1480dcaba5b4b643562061ad0f450600160035500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "604060006040600060003562092856fa600055600160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600160035200")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6040600060406000735ad1f77e14fe15f07a2f5df1480dcaba5b4b643562061ad0f4505b61c3506080511015603f5760013b506001608051016080526023565b00"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "604060006040600073335c5531b84765a7626e6e76688f18b81be5259c6201d4e8fa00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6040600060406000735ad1f77e14fe15f07a2f5df1480dcaba5b4b643562061ad0f450600160035500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "604060006040600060003562092856fa600055600160015500"
                    ),
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
