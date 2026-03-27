"""
The first test case required here.

https://github.com/ethereum/tests/issues/431#issue-306081539

Implements: SUC007.0, SUC007.1, SUC007.2, SUC007.3,
            SUC008.0, SUC008.1, SUC008.2, SUC008.3

Ported from:
state_tests/stSystemOperationsTest/doubleSelfdestructTestFiller.yml
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
    "f110011002",
    "f210011002",
    "f410011002",
    "fa10011002",
    "f11001c0de",
    "f21001c0de",
    "f41001c0de",
    "fa1001c0de",
]
TX_GAS = [16777216]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stSystemOperationsTest/doubleSelfdestructTestFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="called-self-destruct",
        ),
        pytest.param(
            1,
            0,
            0,
            id="called-self-destruct",
        ),
        pytest.param(
            2,
            0,
            0,
            id="called-self-destruct",
        ),
        pytest.param(
            3,
            0,
            0,
            id="caller-self-destruct",
        ),
        pytest.param(
            4,
            0,
            0,
            id="code-self-destruct",
        ),
        pytest.param(
            5,
            0,
            0,
            id="code-self-destruct",
        ),
        pytest.param(
            6,
            0,
            0,
            id="code-self-destruct",
        ),
        pytest.param(
            7,
            0,
            0,
            id="caller-self-destruct",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_double_selfdestruct_test(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """
    The first test case required here
    https://github.
    """
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x000000000000000000000000000000000000c0de")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000000,
    )

    # Source: yul
    # berlin
    # {
    #    // If there's data, call this again and then
    #    // try to selfdestruct.
    #    // Necessary to use data, because delegatecall and staticcall don't
    #    // affect calldata
    #    if gt(calldatasize(), 2) {
    #      // Type of call to make
    #      let opcode := shr(248, calldataload(0))
    #
    #      // Address for caller selfdestruct
    #      let caller_ff := and(shr(232, calldataload(0)), 0xFFFF)
    #
    #      // Address for called selfdestruct, which we need to send with the call  # noqa: E501
    #      let called_ff := and(shr(216, calldataload(0)), 0xFFFF)
    #      mstore8(0, and(shr(8, called_ff), 0xFF))
    #      mstore8(1, and(called_ff, 0xFF))
    #
    #      if eq(opcode, 0xF1) { pop(call(gas(), 0xc0de, 0, 0,2, 0,0)) }
    #      if eq(opcode, 0xF2) { pop(callcode(gas(), 0xc0de, 0, 0,2, 0,0)) }
    #      if eq(opcode, 0xF4) { pop(delegatecall(gas(), 0xc0de, 0,2, 0,0)) }
    #      if eq(opcode, 0xFA) { pop(staticcall(gas(), 0xc0de, 0,2, 0,0)) }
    #      selfdestruct(caller_ff)
    #    }
    #
    #    // If there are only two bytes of call data, that is the
    #    // selfdestruct address
    #    let called_ff := and(shr(240, calldataload(0)), 0xFFFF)
    #    if eq(calldatasize(), 2) {
    #      selfdestruct(called_ff)
    # ... (2 more lines)
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=0x17, condition=Op.GT(Op.CALLDATASIZE, 0x2))
        + Op.SHR(0xF0, Op.CALLDATALOAD(offset=0x0))
        + Op.JUMPI(pc=0x15, condition=Op.EQ(0x2, Op.CALLDATASIZE))
        + Op.STOP
        + Op.JUMPDEST
        + Op.SELFDESTRUCT
        + Op.JUMPDEST
        + Op.SHR(0xF8, Op.CALLDATALOAD(offset=0x0))
        + Op.PUSH1[0xFA]
        + Op.AND(Op.SHR(0xE8, Op.CALLDATALOAD(offset=0x0)), 0xFFFF)
        + Op.SWAP2
        + Op.PUSH1[0xFF]
        + Op.AND(Op.SHR(0xD8, Op.CALLDATALOAD(offset=0x0)), 0xFFFF)
        + Op.MSTORE8(offset=0x0, value=Op.AND(Op.SHR(0x8, Op.DUP2), Op.DUP2))
        + Op.MSTORE8(offset=0x1, value=Op.AND)
        + Op.JUMPI(pc=0x90, condition=Op.EQ(Op.DUP2, 0xF1))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x7F, condition=Op.EQ(Op.DUP2, 0xF2))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x6F, condition=Op.EQ(Op.DUP2, 0xF4))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x61, condition=Op.EQ)
        + Op.SELFDESTRUCT
        + Op.JUMPDEST
        + Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=0xC0DE,
                args_offset=Op.DUP2,
                args_size=0x2,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.SELFDESTRUCT
        + Op.JUMPDEST
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=0xC0DE,
                args_offset=Op.DUP2,
                args_size=0x2,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.JUMP(pc=0x5B)
        + Op.JUMPDEST
        + Op.POP(
            Op.CALLCODE(
                gas=Op.GAS,
                address=0xC0DE,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x2,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.JUMP(pc=0x53)
        + Op.JUMPDEST
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xC0DE,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=0x2,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.JUMP(pc=0x4B),
        balance=0xF4240,
        nonce=1,
        address=Address("0x000000000000000000000000000000000000c0de"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 1, 2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(
                    "0x0000000000000000000000000000000000001001"
                ): Account.NONEXISTENT,
                Address("0x0000000000000000000000000000000000001002"): Account(
                    balance=0xF4241
                ),
            },
        },
        {
            "indexes": {"data": [3, 7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x0000000000000000000000000000000000001001"): Account(
                    balance=0xF4241, nonce=0
                ),
                Address(
                    "0x0000000000000000000000000000000000001002"
                ): Account.NONEXISTENT,
                contract_0: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": [4, 5, 6], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x0000000000000000000000000000000000001001"): Account(
                    balance=0xF4241, nonce=0
                ),
                contract_0: Account(nonce=1),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=1,
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
