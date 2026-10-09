"""
Test_random_statetest233.

Ported from:
state_tests/stRandom/randomStatetest233Filler.json
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
    ["state_tests/stRandom/randomStatetest233Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest233(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest233."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe817fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff42057f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff517f000000000000000000000001000000000000000000000000000000000000000065715460005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.DUP2
        + Op.SDIV(
            Op.TIMESTAMP,
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        )
        + Op.MLOAD(
            offset=Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        )
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH6[0x715460005155],
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
            "7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe817fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff42057f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff517f0000000000000000000000010000000000000000000000000000000000000000657154"  # noqa: E501
        ),
        gas_limit=100000,
        value=0x77B5363E,
    )

    post = {
        target: Account(storage={}, balance=0, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
