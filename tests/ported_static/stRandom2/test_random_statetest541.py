"""
Test_random_statetest541.

Ported from:
state_tests/stRandom2/randomStatetest541Filler.json

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
    ["state_tests/stRandom2/randomStatetest541Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest541(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest541."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff457f000000000000000000000000000000000000000000000000000000000000c3507f00000000000000000000000000000000000000000000000000000000000000017f00000000000000000000000000000000000000000000000000000000000000007f00000000000000000000000100000000000000000000000000000000000000004335696e089257368d07897d57350b105560005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.GASLIMIT
        + Op.PUSH32[0xC350]
        + Op.PUSH32[0x1]
        + Op.SSTORE(
            key=Op.LT(
                Op.SIGNEXTEND(
                    Op.CALLDATALOAD(offset=0x6E089257368D07897D57),
                    Op.CALLDATALOAD(offset=Op.NUMBER),
                ),
                Op.PUSH32[0x10000000000000000000000000000000000000000],
            ),
            value=Op.PUSH32[0x0],
        )
        + Op.MLOAD(offset=0x0)
        + Op.SSTORE,
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
            "7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff457f000000000000000000000000000000000000000000000000000000000000c3507f00000000000000000000000000000000000000000000000000000000000000017f00000000000000000000000000000000000000000000000000000000000000007f00000000000000000000000100000000000000000000000000000000000000004335696e089257368d07897d57350b10"  # noqa: E501
        ),
        value=0x1F529315,
    )

    post = {
        target: Account(storage={0: 1}, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
