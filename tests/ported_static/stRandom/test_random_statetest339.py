"""
Test_random_statetest339.

Ported from:
state_tests/stRandom/randomStatetest339Filler.json

@manually-enhanced: Do not overwrite. tx `gas_limit` has been removed.
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
    ["state_tests/stRandom/randomStatetest339Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest339(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest339."""
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
    # 0x7f00000000000000000000000000000000000000000000000000000000000000017f00000000000000000000000000000000000000000000000000000000000000007f00000000000000000000000000000000000000000000000000000000000000017f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7f00000000000000000000000100000000000000000000000000000000000000007f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000000000000000000000000000000000000000c3506f89029e850708a293905668f1a367a25560005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[0x1]
        + Op.PUSH32[0x0]
        + Op.PUSH32[0x1]
        + Op.PUSH32[0x0]
        + Op.PUSH32[coinbase]
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH32[0x0]
        + Op.PUSH32[0xC350]
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0), value=0x89029E850708A293905668F1A367A255
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[0x1]
            + Op.PUSH32[0x0]
            + Op.PUSH32[0x1]
            + Op.PUSH32[0x0]
            + Op.PUSH32[coinbase]
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.PUSH32[0x0]
            + Op.PUSH32[0xC350]
            + Bytes("6f89029e850708a293905668f1a367a2")
        ),
        value=0x3F78C8AA,
    )

    post = {
        target: Account(
            storage={0: 0x89029E850708A293905668F1A367A255},
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
