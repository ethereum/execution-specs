"""
Test_random_statetest571.

Ported from:
state_tests/stRandom2/randomStatetest571Filler.json

@manually-enhanced: Do not overwrite. Explicit gas values removed.
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
    ["state_tests/stRandom2/randomStatetest571Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest571(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest571."""
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
    # 0x7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000015b7f00000000000000000000000100000000000000000000000000000000000000007f00000000000000000000000000000000000000000000000000000000000000017f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>3c6508766c8b6b403a60005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        * 2
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.PUSH32[0x1]
        + Op.JUMPDEST
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH32[0x1]
        + Op.PUSH32[coinbase]
        + Op.EXTCODECOPY
        + Op.PUSH6[0x8766C8B6B40]
        + Op.SSTORE(key=Op.MLOAD(offset=0x0), value=Op.GASPRICE),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            * 2
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[0x1]
            + Op.JUMPDEST
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.PUSH32[0x1]
            + Op.PUSH32[coinbase]
            + Op.EXTCODECOPY
            + Op.PUSH6[0x8766C8B6B40]
            + Op.GASPRICE
        ),
        value=0x53934784,
    )

    post = {
        target: Account(storage={0: 10}, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
