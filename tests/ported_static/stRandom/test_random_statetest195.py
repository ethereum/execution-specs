"""
Test_random_statetest195.

Ported from:
state_tests/stRandom/randomStatetest195Filler.json

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
    ["state_tests/stRandom/randomStatetest195Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest195(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest195."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x7f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000000000000000000000000000000000000000c350417fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff097f000000000000000000000001000000000000000000000000000000000000000055  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[0xC350] * 2
        + Op.COINBASE
        + Op.SSTORE(
            key=Op.PUSH32[0x10000000000000000000000000000000000000000],
            value=Op.MULMOD(
                Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF],
                Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF],
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            ),
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
            "7f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000000000000000000000000000000000000000c350417fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff097f0000000000000000000000010000000000000000000000000000000000000000"  # noqa: E501
        ),
        value=0x1252A41F,
    )

    post = {
        target: Account(
            storage={
                0x10000000000000000000000000000000000000000: 0xFFFFFFFFFFFFFFFFFFFFFFFE0000000000000000000000010000000000000000,  # noqa: E501
            },
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
