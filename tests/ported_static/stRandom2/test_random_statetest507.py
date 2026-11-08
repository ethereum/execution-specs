"""
Test_random_statetest507.

Ported from:
state_tests/stRandom2/randomStatetest507Filler.json
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

from tests.ported_static.constants import HIGH_GAS_LIMIT

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom2/randomStatetest507Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
def test_random_statetest507(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest507."""
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
    # 0x5a7f0000000000000000000000010000000000000000000000000000000000000000327f00000000000000000000000000000000000000000000000000000000000000017f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>6f99a4527612a199a06d1a348b02563a9b60005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.GAS
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.ORIGIN
        + Op.PUSH32[0x1]
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.PUSH32[coinbase]
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0), value=0x99A4527612A199A06D1A348B02563A9B
        ),
    )

    env = Environment(
        fee_recipient=coinbase, prev_randao=0x20000, gas_limit=HIGH_GAS_LIMIT
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.GAS
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.ORIGIN
            + Op.PUSH32[0x1]
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Op.PUSH32[coinbase]
            + Op.PUSH16[0x99A4527612A199A06D1A348B02563A9B]
        ),
        gas_limit=1868758461,
        value=0x2987830A,
    )

    post = {
        target: Account(
            storage={0: 0x99A4527612A199A06D1A348B02563A9B},
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
