"""
Test_random_statetest534.

Ported from:
state_tests/stRandom2/randomStatetest534Filler.json

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
    ["state_tests/stRandom2/randomStatetest534Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest534(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest534."""
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
    # 0x7f000000000000000000000001000000000000000000000000000000000000000045437f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff457f0000000000000000000000000000000000000000000000000000000000000000436ff3075243846d88747b6a9e7ff28c615560005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.GASLIMIT
        + Op.NUMBER
        + Op.PUSH32[coinbase]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        + Op.GASLIMIT
        + Op.PUSH32[0x0]
        + Op.NUMBER
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0), value=0xF3075243846D88747B6A9E7FF28C6155
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.GASLIMIT
            + Op.NUMBER
            + Op.PUSH32[coinbase]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Op.GASLIMIT
            + Op.PUSH32[0x0]
            + Op.NUMBER
            + Bytes("6ff3075243846d88747b6a9e7ff28c61")
        ),
        value=0x55DB76C1,
    )

    post = {
        target: Account(
            storage={0: 0xF3075243846D88747B6A9E7FF28C6155},
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
