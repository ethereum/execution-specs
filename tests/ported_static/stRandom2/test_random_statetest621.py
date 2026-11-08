"""
Test_random_statetest621.

Ported from:
state_tests/stRandom2/randomStatetest621Filler.json

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
    ["state_tests/stRandom2/randomStatetest621Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest621(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest621."""
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
    # 0x7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7f0000000000000000000000000000000000000000000000000000000000000000441a7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff6f3ba187a19366899e595220741232905b60005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.PUSH32[coinbase] * 2
        + Op.BYTE(Op.PREVRANDAO, Op.PUSH32[0x0])
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0), value=0x3BA187A19366899E595220741232905B
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[coinbase] * 2
            + Op.BYTE(Op.PREVRANDAO, Op.PUSH32[0x0])
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0x3BA187A19366899E595220741232905B]
        ),
        value=0x7FC94217,
    )

    post = {
        target: Account(
            storage={0: 0x3BA187A19366899E595220741232905B},
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
