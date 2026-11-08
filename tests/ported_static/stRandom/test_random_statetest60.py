"""
Test_random_statetest60.

Ported from:
state_tests/stRandom/randomStatetest60Filler.json

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
    ["state_tests/stRandom/randomStatetest60Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest60(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest60."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x427f0000000000000000000000000000000000000000000000000000000000000000427f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff437f000000000000000000000000000000000000000000000000000000000000c3507ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe6f969001091aa15b8b9b75459d015a045560005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.TIMESTAMP
        + Op.PUSH32[0x0]
        + Op.TIMESTAMP
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.NUMBER
        + Op.PUSH32[0xC350]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0), value=0x969001091AA15B8B9B75459D015A0455
        ),
    )
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

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "427f0000000000000000000000000000000000000000000000000000000000000000427f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff437f000000000000000000000000000000000000000000000000000000000000c3507ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe6f969001091aa15b8b9b75459d015a04"  # noqa: E501
        ),
        value=0x54DE1EAF,
    )

    post = {
        target: Account(
            storage={0: 0x969001091AA15B8B9B75459D015A0455},
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
