"""
Test_random_statetest28.

Ported from:
state_tests/stRandom/randomStatetest28Filler.json

@manually-enhanced: Do not overwrite. tx `gas_limit` has been removed.
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
    ["state_tests/stRandom/randomStatetest28Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest28(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest28."""
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
    # 0x7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff417f00000000000000000000000100000000000000000000000000000000000000007f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>6f38129d68939a19a2697172926f6a67363055  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        * 2
        + Op.COINBASE
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH32[coinbase]
        + Op.SSTORE(key=Op.ADDRESS, value=0x38129D68939A19A2697172926F6A6736),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            * 2
            + Op.COINBASE
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.PUSH32[coinbase]
            + Op.PUSH16[0x38129D68939A19A2697172926F6A6736]
            + Op.ADDRESS
        ),
        value=0x51AF41E7,
    )

    post = {
        target: Account(
            storage={
                target: 0x38129D68939A19A2697172926F6A6736,  # noqa: E501
            },
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
