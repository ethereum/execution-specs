"""
Test_random_statetest200.

Ported from:
state_tests/stRandom/randomStatetest200Filler.json

@manually-enhanced: Do not overwrite. tx `gas_limit` has been removed.
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
    ["state_tests/stRandom/randomStatetest200Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest200(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest200."""
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
    # 0x437f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000100000000000000000000000000000000000000007f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>346f42051af2a24050039e9d3a678b028a0a8055  # noqa: E501
    target = pre.deploy_contract(
        code=Op.NUMBER
        + Op.PUSH32[0xC350]
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH32[coinbase]
        + Op.CALLVALUE
        + Op.SSTORE(key=Op.DUP1, value=0x42051AF2A24050039E9D3A678B028A0A),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.NUMBER
            + Op.PUSH32[0xC350]
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.PUSH32[coinbase]
            + Op.CALLVALUE
            + Op.PUSH16[0x42051AF2A24050039E9D3A678B028A0A]
            + Op.DUP1
        ),
        value=0x3F51031D,
    )

    post = {
        target: Account(
            storage={
                0x42051AF2A24050039E9D3A678B028A0A: 0x42051AF2A24050039E9D3A678B028A0A,  # noqa: E501
            },
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
