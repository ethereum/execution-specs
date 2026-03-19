"""
Implements: SUC000, SUC001, SUC002, SUC003, SUC004, SUC005.

Ported from:
tests/static/state_tests/stSystemOperationsTest/multiSelfdestructFiller.yml
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
    "01",
    "02",
    "03",
    "04",
    "05",
]

TX_GAS = [10000000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stSystemOperationsTest/multiSelfdestructFiller.yml",  # noqa: E501
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
        pytest.param(4, 0, 0, id="case4"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_multi_selfdestruct(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Implements: SUC000, SUC001, SUC002, SUC003, SUC004, SUC005."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=71794957647893862,
    )

    # Source: Yul
    # {
    #    let operation := shr(248, calldataload(0))
    #    let recipient := and(shr(232, calldataload(0)), 0xFFFF)
    #
    #    // Don't do anything
    #    if eq(operation, 0) {
    #      stop()
    #    }
    #
    #    // Selfdestruct
    #    if eq(operation, 0xFF) {
    #      selfdestruct(recipient)
    #    }
    #
    #    // Send value
    #    // If the call fails, revert
    #    if eq(call(gas(), recipient, operation, 0,0, 0,0),0) {
    #       revert(0,0)
    #    }
    #
    # }
    callee = pre.deploy_contract(
        code=(
            Op.SHR(0xF8, Op.CALLDATALOAD(offset=0x0))
            + Op.AND(Op.SHR(0xE8, Op.CALLDATALOAD(offset=0x0)), 0xFFFF)
            + Op.JUMPI(pc=0x34, condition=Op.EQ(Op.DUP3, 0x0))
            + Op.JUMPI(pc=0x32, condition=Op.EQ(Op.DUP3, 0xFF))
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
            + Op.SWAP5
            + Op.DUP2
            + Op.SWAP5
            + Op.JUMPI(pc=0x2D, condition=Op.EQ(Op.CALL, Op.GAS))
            + Op.STOP
            + Op.JUMPDEST
            + Op.REVERT(offset=Op.DUP1, size=0x0)
            + Op.JUMPDEST
            + Op.SELFDESTRUCT
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=3,
        address=Address("0x000000000000000000000000000000000000dead"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)
    # Source: Yul
    # {
    #    let delme
    #
    #    // Selfdestruct, send balance to 0x1000
    #    // SUC000
    #    mstore8(0, 0xFF)
    #    mstore8(1, 0x10)
    #    mstore8(2, 0x00)
    #    delme := call(gas(), 0xdead, 0, 0,3, 0,0)
    #    sstore(0x00, delme)
    #    sstore(0x01, balance(0x1000))
    #    sstore(0x02, balance(0xdead))
    #
    #    let test := shr(248, calldataload(0))
    #    switch test
    #    case 1 {
    #        // call with all zeros, so it won't do anything
    #        delme := call(gas(), 0xdead, 2, 3,3, 0,0)
    #    }
    #    case 2 {
    #        // Another suicide to 0x1000
    #        delme := call(gas(), 0xdead, 2, 0,3, 0,0)
    #    }
    #    case 3 {
    #        // Suicide to 0x1001
    #        mstore8(2, 1)
    #        delme := call(gas(), 0xdead, 2, 0,3, 0,0)
    #    }
    #    case 4 {
    #        // Attempt to transfer WEI you don't have to 0x1001
    # ... (21 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x0, value=0xFF)
            + Op.MSTORE8(offset=0x1, value=0x10)
            + Op.MSTORE8(offset=0x2, value=0x0)
            + Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=0xDEAD,
                    value=Op.DUP1,
                    args_offset=Op.DUP2,
                    args_size=0x3,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.BALANCE(address=0x1000))
            + Op.SSTORE(key=0x2, value=Op.BALANCE(address=0xDEAD))
            + Op.SHR(0xF8, Op.CALLDATALOAD(offset=0x0))
            + Op.JUMPI(pc=0xCE, condition=Op.EQ(0x1, Op.DUP1))
            + Op.JUMPI(pc=0xBC, condition=Op.EQ(0x2, Op.DUP1))
            + Op.JUMPI(pc=0xA5, condition=Op.EQ(0x3, Op.DUP1))
            + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x4, Op.DUP1))
            + Op.PUSH1[0x5]
            + Op.JUMPI(pc=0x58, condition=Op.EQ)
            + Op.REVERT(offset=Op.DUP1, size=0x0)
            + Op.JUMPDEST
            + Op.MSTORE8(offset=0x0, value=0x1)
            + Op.MSTORE8(offset=0x2, value=0x1)
            + Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x2,
                args_offset=Op.DUP2,
                args_size=0x3,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.PUSH1[0x10]
            + Op.SSTORE
            + Op.SSTORE(key=0x11, value=Op.BALANCE(address=0x1000))
            + Op.SSTORE(key=0x12, value=Op.BALANCE(address=0xDEAD))
            + Op.SSTORE(key=0x13, value=Op.BALANCE(address=0x1001))
            + Op.STOP
            + Op.JUMPDEST
            + Op.POP
            + Op.MSTORE8(offset=0x0, value=0x1)
            + Op.MSTORE8(offset=0x2, value=0x1)
            + Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x3,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.JUMP(pc=0x70)
            + Op.JUMPDEST
            + Op.POP
            + Op.MSTORE8(offset=0x2, value=0x1)
            + Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x2,
                args_offset=Op.DUP2,
                args_size=0x3,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.JUMP(pc=0x70)
            + Op.JUMPDEST
            + Op.POP
            + Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x2,
                args_offset=Op.DUP2,
                args_size=0x3,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.JUMP(pc=0x70)
            + Op.JUMPDEST
            + Op.POP
            + Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=0x2,
                args_offset=Op.DUP1,
                args_size=0x3,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.JUMP(pc=0x70)
        ),
        storage={
            0x0: 0x60A7,
            0x1: 0x60A7,
            0x10: 0x60A7,
            0x11: 0x60A7,
            0x12: 0x60A7,
            0x13: 0x60A7,
        },
        balance=0x5F5E100,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(nonce=1, balance=2),
                contract: Account(
                    storage={0: 1, 1: 3, 2: 0, 16: 1, 17: 3, 18: 2}
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(nonce=1, balance=0),
                contract: Account(
                    storage={0: 1, 1: 3, 2: 0, 16: 1, 17: 5, 18: 0}
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(nonce=1, balance=0),
                contract: Account(
                    storage={0: 1, 1: 3, 2: 0, 16: 1, 17: 3, 18: 0, 19: 2}
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(nonce=1, balance=0),
                contract: Account(
                    storage={0: 1, 1: 3, 2: 0, 16: 0, 17: 3, 18: 0, 19: 0}
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(nonce=1, balance=1),
                contract: Account(
                    storage={0: 1, 1: 3, 2: 0, 16: 1, 17: 3, 18: 1, 19: 1}
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
        gas_price=1000,
        nonce=1,
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
