"""
Test_random_statetest409.

Ported from:
state_tests/stRandom2/randomStatetest409Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Amsterdam
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom2/randomStatetest409Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest409(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_random_statetest409."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x6000355415600957005b60203560003555
    coinbase = pre.deploy_contract(
        code=Op.JUMPI(
            pc=0x9,
            condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
        )
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(
            key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)
        ),
        balance=46,
    )
    # Source: raw
    # 0x5b7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000100000000000000000000000000000000000000007f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000001000000000000000000000000000000000000000009ff511287868833063aa3579d8e585560005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH32[coinbase]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        + Op.SELFDESTRUCT(
            address=Op.MULMOD(
                Op.PUSH32[0x10000000000000000000000000000000000000000],
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
        )
        + Op.MLOAD
        + Op.LOG3(
            offset=Op.GASPRICE,
            size=Op.MOD(Op.CALLER, Op.DUP9),
            topic_1=Op.DUP7,
            topic_2=Op.DUP8,
            topic_3=Op.SLT,
        )
        + Op.JUMPI
        + Op.SWAP14
        + Op.SSTORE(key=Op.PC, value=Op.DUP15)
        + Op.MLOAD(offset=0x0)
        + Op.SSTORE,
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.JUMPDEST
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.PUSH32[coinbase]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Op.SELFDESTRUCT(
                address=Op.MULMOD(
                    Op.PUSH32[0x10000000000000000000000000000000000000000],
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                )
            )
            + Op.MLOAD
            + Op.LOG3(
                offset=Op.GASPRICE,
                size=Op.MOD(Op.CALLER, Op.DUP9),
                topic_1=Op.DUP7,
                topic_2=Op.DUP8,
                topic_3=Op.SLT,
            )
            + Op.JUMPI
            + Op.SWAP14
            + Op.DUP15
            + Op.PC
        ),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
        value=0x41028C83,
    )

    post = {
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
        Address(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF): Account(
            storage={}, code=b"", balance=0x41028C83, nonce=0
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
