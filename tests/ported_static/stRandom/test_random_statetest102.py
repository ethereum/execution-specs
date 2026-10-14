"""
Test_random_statetest102.

Ported from:
state_tests/stRandom/randomStatetest102Filler.json

@manually-enhanced: Do not overwrite. Explicit gas values removed.
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
    ["state_tests/stRandom/randomStatetest102Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest102(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest102."""
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
    # 0x457f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>44447f00000000000000000000000000000000000000000000000000000000000000007f00000000000000000000000000000000000000000000000000000000000000007f00000000000000000000000000000000000000000000000000000000000000017ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe6f157094ffff1a04893a9cf3858b85765560005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.GASLIMIT
        + Op.PUSH32[coinbase]
        + Op.PREVRANDAO * 2
        + Op.PUSH32[0x0] * 2
        + Op.PUSH32[0x1]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0), value=0x157094FFFF1A04893A9CF3858B857655
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.GASLIMIT
            + Op.PUSH32[coinbase]
            + Op.PREVRANDAO * 2
            + Op.PUSH32[0x0] * 2
            + Op.PUSH32[0x1]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Bytes("6f157094ffff1a04893a9cf3858b8576")
        ),
        value=0x25D01AE2,
    )

    post = {
        target: Account(
            storage={0: 0x157094FFFF1A04893A9CF3858B857655},
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
