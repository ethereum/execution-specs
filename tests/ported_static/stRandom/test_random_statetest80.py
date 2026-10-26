"""
Test_random_statetest80.

Ported from:
state_tests/stRandom/randomStatetest80Filler.json

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
    ["state_tests/stRandom/randomStatetest80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest80(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest80."""
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
    # 0x7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f0000000000000000000000010000000000000000000000000000000000000000117fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7e7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b5681069127b3b9c877d6f6169ff3660005155  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.PUSH32[coinbase]
        + Op.PUSH32[0xC350]
        + Op.GT(
            Op.PUSH32[0x10000000000000000000000000000000000000000],
            Op.PUSH32[coinbase],
        )
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        + Op.SSTORE(
            key=0xB5681069127B3B9C877D6F6169FF36600051,
            value=0x7F000000000000000000000000945304EB96065B2A98B57A48A06AE28D285A,  # noqa: E501
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=(
            Op.PUSH32[coinbase]
            + Op.PUSH32[0xC350]
            + Op.GT(
                Op.PUSH32[0x10000000000000000000000000000000000000000],
                Op.PUSH32[coinbase],
            )
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Bytes("7e7f000000000000000000000000")
            + coinbase
            + Bytes("681069127b3b9c877d6f6169ff36")
        ),
        value=0x1ED9A5B6,
    )

    post = {
        contract_0: Account(
            storage={
                0xB5681069127B3B9C877D6F6169FF36600051: 0x7F000000000000000000000000945304EB96065B2A98B57A48A06AE28D285A,  # noqa: E501
            },
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
