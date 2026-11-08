"""
Test_random_statetest378.

Ported from:
state_tests/stRandom/randomStatetest378Filler.json
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

from tests.ported_static.constants import HIGH_GAS_LIMIT

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom/randomStatetest378Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
def test_random_statetest378(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest378."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff547f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000017f000000000000000000000000000000000000000000000000000000000000c3507f00000000000000000000000000000000000000000000000000000000000000005a7f00000000000000000000000000000000000000000000000000000000000000016f855b445834721a5706f2891711f0025560005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SLOAD(
            key=Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        )
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.PUSH32[0x1]
        + Op.PUSH32[0xC350]
        + Op.PUSH32[0x0]
        + Op.GAS
        + Op.PUSH32[0x1]
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0), value=0x855B445834721A5706F2891711F00255
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

    env = Environment(
        fee_recipient=coinbase, prev_randao=0x20000, gas_limit=HIGH_GAS_LIMIT
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff547f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000017f000000000000000000000000000000000000000000000000000000000000c3507f00000000000000000000000000000000000000000000000000000000000000005a7f00000000000000000000000000000000000000000000000000000000000000016f855b445834721a5706f2891711f002"  # noqa: E501
        ),
        gas_limit=1231102875,
        value=0x63E033B2,
    )

    post = {
        target: Account(
            storage={0: 0x855B445834721A5706F2891711F00255},
            balance=0x63E033B2,
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
