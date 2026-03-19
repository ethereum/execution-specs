"""
Danno Ferrin danno.ferrin@gmail.com.

Ported from:
tests/static/state_tests/stEIP150Specific
Transaction64Rule_integerBoundariesFiller.yml
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
    "000000000000000000000000000000000000000000000000000000000000007f",
    "000000000000000000000000000000000000000000000000000000000000008f",
    "0000000000000000000000000000000000000000000000000000000000007fff",
    "0000000000000000000000000000000000000000000000000000000000008fff",
    "000000000000000000000000000000000000000000000000000000007fffffff",
    "000000000000000000000000000000000000000000000000000000008fffffff",
    "0000000000000000000000000000000000000000000000007fffffffffffffff",
    "0000000000000000000000000000000000000000000000008fffffffffffffff",
    "000000000000000000000000000000007fffffffffffffffffffffffffffffff",
    "000000000000000000000000000000008fffffffffffffffffffffffffffffff",
    "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    "8fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
]

TX_GAS = [800000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stEIP150Specific/Transaction64Rule_integerBoundariesFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(8, 0, 0, id="case0"),
        pytest.param(2, 0, 0, id="case1"),
        pytest.param(10, 0, 0, id="case2"),
        pytest.param(4, 0, 0, id="case3"),
        pytest.param(6, 0, 0, id="case4"),
        pytest.param(0, 0, 0, id="case5"),
        pytest.param(9, 0, 0, id="case6"),
        pytest.param(3, 0, 0, id="case7"),
        pytest.param(11, 0, 0, id="case8"),
        pytest.param(5, 0, 0, id="case9"),
        pytest.param(7, 0, 0, id="case10"),
        pytest.param(1, 0, 0, id="case11"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_transaction64_rule_integer_boundaries(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Danno Ferrin danno.ferrin@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.PUSH1[0xFF] + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   let initialgas := gas()
    #   let callgas := calldataload(0)
    #
    #   pop(call(callgas, 0x1000, 0, 0, 0, 0, 0x20))
    #   sstore(0, lt(gas(), initialgas))
    #
    #   pop(callcode(callgas, 0x1000, 0, 0, 0, 0, 0x20))
    #   sstore(1, lt(gas(), initialgas))
    #
    #   pop(delegatecall(callgas, 0x1000, 0, 0x20, 0, 0x20))
    #   sstore(2, lt(gas(), initialgas))
    #
    #   pop(staticcall(callgas, 0x1000, 0, 0x20, 0, 0x20))
    #   sstore(3, lt(gas(), initialgas))
    # }
    contract = pre.deploy_contract(
        code=(
            Op.GAS
            + Op.PUSH1[0x20]
            + Op.PUSH1[0x0]
            + Op.DUP2
            + Op.DUP2
            + Op.PUSH2[0x1000]
            + Op.CALLDATALOAD(offset=Op.DUP2)
            + Op.POP(
                Op.CALL(
                    gas=Op.DUP7,
                    address=Op.DUP7,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP4,
                    ret_size=Op.DUP4,
                ),
            )
            + Op.SSTORE(key=Op.DUP4, value=Op.LT(Op.GAS, Op.DUP7))
            + Op.POP(
                Op.CALLCODE(
                    gas=Op.DUP7,
                    address=Op.DUP7,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP4,
                    ret_size=Op.DUP4,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.LT(Op.GAS, Op.DUP7))
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.DUP6,
                    address=Op.DUP6,
                    args_offset=Op.DUP2,
                    args_size=Op.DUP2,
                    ret_offset=Op.DUP4,
                    ret_size=Op.DUP4,
                ),
            )
            + Op.SSTORE(key=0x2, value=Op.LT(Op.GAS, Op.DUP7))
            + Op.POP(Op.STATICCALL)
            + Op.GAS
            + Op.SSTORE(key=0x3, value=Op.LT)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000c0de"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x10000000000000000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": -1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract: Account(storage={0: 1, 1: 1, 2: 1, 3: 1})},
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
