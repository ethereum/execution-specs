"""
Test_random_statetest565.

Ported from:
state_tests/stRandom2/randomStatetest565Filler.json

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
    ["state_tests/stRandom2/randomStatetest565Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest565(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest565."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x7f00000000000000000000000100000000000000000000000000000000000000007f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000000000000000000000000000000000000000000000000000c350137f000000000000000000000000000000000000000000000000000000000000c3507f00000000000000000000000000000000000000000000000000000000000000007f0000000000000000000000010000000000000000000000000000000000000000923760005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.SGT(
            Op.PUSH32[0xC350],
            Op.PUSH32[0x945304EB96065B2A98B57A48A06AE28D285A71B5],
        )
        + Op.PUSH32[0xC350]
        + Op.PUSH32[0x0]
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.SWAP3
        + Op.CALLDATACOPY
        + Op.MLOAD(offset=0x0)
        + Op.SSTORE,
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
            "7f00000000000000000000000100000000000000000000000000000000000000007f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000000000000000000000000000000000000000000000000000c350137f000000000000000000000000000000000000000000000000000000000000c3507f00000000000000000000000000000000000000000000000000000000000000007f00000000000000000000000100000000000000000000000000000000000000009237"  # noqa: E501
        ),
        value=0x28CD0966,
    )

    post = {
        target: Account(
            storage={
                0x7F00000000000000000000000100000000000000000000000000000000000000: 0x10000000000000000000000000000000000000000,  # noqa: E501
            },
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
