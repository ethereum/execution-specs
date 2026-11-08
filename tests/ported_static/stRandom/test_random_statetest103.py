"""
Test_random_statetest103.

Ported from:
state_tests/stRandom/randomStatetest103Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom/randomStatetest103Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest103(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest103."""
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
    # 0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe92357fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff597f00000000000000000000000000000000000000000000000000000000000000019385a39988160a205a93196d336428  # noqa: E501
    target = pre.deploy_contract(
        code=(
            Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Op.PUSH32[coinbase]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Op.SWAP3
            + Op.CALLDATALOAD
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Op.MSIZE
            + Op.PUSH32[0x1]
            + Op.SWAP4
            + Op.DUP6
            + Op.LOG3
            + Op.SWAP10
            + Op.EXP(Op.AND, Op.DUP9)
            + Op.SHA3
            + Op.GAS
            + Op.SWAP4
            + Op.NOT
            + bytes.fromhex("6d336428")
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Op.PUSH32[coinbase]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Op.SWAP3
            + Op.CALLDATALOAD
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Op.MSIZE
            + Op.PUSH32[0x1]
            + Op.SWAP4
            + Op.DUP6
            + Op.LOG3
            + Op.SWAP10
            + Op.EXP(Op.AND, Op.DUP9)
            + Op.SHA3
            + Op.GAS
            + Op.SWAP4
            + Op.NOT
            + Bytes("6d336428")
        ),
        gas_limit=100000,
        value=0x5EF1042E,
    )

    post = {
        target: Account(storage={}, balance=0, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
