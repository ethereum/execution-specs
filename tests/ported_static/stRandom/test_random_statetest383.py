"""
Test_random_statetest383.

Ported from:
state_tests/stRandom/randomStatetest383Filler.json

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
    ["state_tests/stRandom/randomStatetest383Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest383(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest383."""
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
    # 0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff09150255436c75107e  # noqa: E501
    target = pre.deploy_contract(
        code=(
            Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Op.PUSH32[coinbase]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Op.SSTORE(
                key=Op.MUL(
                    Op.ISZERO(
                        Op.MULMOD(
                            Op.PUSH32[
                                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                            ],
                            Op.PUSH32[
                                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                            ],
                            Op.PUSH32[
                                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                            ],
                        )
                    ),
                    Op.PUSH32[coinbase],
                ),
                value=Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF],
            )
            + Op.NUMBER
            + bytes.fromhex("6c75107e")
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Op.PUSH32[coinbase]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Op.SSTORE(
                key=Op.MUL(
                    Op.ISZERO(
                        Op.MULMOD(
                            Op.PUSH32[
                                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                            ],
                            Op.PUSH32[
                                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                            ],
                            Op.PUSH32[
                                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                            ],
                        )
                    ),
                    Op.PUSH32[coinbase],
                ),
                value=Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF],
            )
            + Op.NUMBER
            + Bytes("6c75107e")
        ),
        value=0x6379C077,
    )

    post = {
        target: Account(
            storage={
                coinbase: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            },
            balance=0x6379C077,
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
