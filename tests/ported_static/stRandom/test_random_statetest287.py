"""
Test_random_statetest287.

Ported from:
state_tests/stRandom/randomStatetest287Filler.json
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
    ["state_tests/stRandom/randomStatetest287Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest287(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest287."""
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
    # 0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000017f00000000000000000000000000000000000000000000000000000000000000007f00000000000000000000000100000000000000000000000000000000000000007ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>ff7f00000000000000000000000100000000000000000000000000000000000000000759  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        + Op.PUSH32[0x1]
        + Op.PUSH32[0x0]
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.SELFDESTRUCT(address=Op.PUSH32[coinbase])
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.SMOD
        + Op.MSIZE,
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Op.PUSH32[0x1]
            + Op.PUSH32[0x0]
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Op.SELFDESTRUCT(address=Op.PUSH32[coinbase])
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.SMOD
            + Op.MSIZE
        ),
        gas_limit=15653489,
        value=0x53DC1967,
    )

    post = {
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
