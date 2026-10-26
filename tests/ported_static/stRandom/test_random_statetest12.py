"""
Test_random_statetest12.

Ported from:
state_tests/stRandom/randomStatetest12Filler.json

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
    ["state_tests/stRandom/randomStatetest12Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest12(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest12."""
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
    # 0x7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7f00000000000000000000000100000000000000000000000000000000000000007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff457ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>027f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff6f165490a41215369ef27603794116335560005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[coinbase]
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        + Op.GASLIMIT
        + Op.MUL(
            Op.PUSH32[coinbase],
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
        )
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0), value=0x165490A41215369EF276037941163355
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[coinbase]
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Op.GASLIMIT
            + Op.MUL(
                Op.PUSH32[coinbase],
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
            )
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Bytes("6f165490a41215369ef2760379411633")
        ),
        value=0x4576EB63,
    )

    post = {
        target: Account(
            storage={0: 0x165490A41215369EF276037941163355},
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
