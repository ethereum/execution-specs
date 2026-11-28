"""
Test_random_statetest507.

Ported from:
state_tests/stRandom2/randomStatetest507Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom2/randomStatetest507Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest507(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest507."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

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
    target = pre.deploy_contract(
        code=Op.GAS
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.ORIGIN
        + Op.PUSH32[0x1]
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.PUSH32[coinbase]
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0), value=0x99A4527612A199A06D1A348B02563A9B
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.GAS
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.ORIGIN
            + Op.PUSH32[0x1]
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Op.PUSH32[coinbase]
            + Op.PUSH16[0x99A4527612A199A06D1A348B02563A9B]
        ),
        value=0x2987830A,
    )

    post = {
        target: Account(
            storage={0: 0x99A4527612A199A06D1A348B02563A9B},
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
