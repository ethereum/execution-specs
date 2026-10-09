"""
Test_random_statetest454.

Ported from:
state_tests/stRandom2/randomStatetest454Filler.json
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
    ["state_tests/stRandom2/randomStatetest454Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest454(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest454."""
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
    # 0x7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f0000000000000000000000000000000000000000000000000000000000000000557f00000000000000000000000000000000000000000000000000000000000000007f0000000000000000000000000000000000000000000000000000000000000000557f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>0a84339188646595668352a061855560005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=Op.PUSH32[0x0],
            value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
        )
        + Op.SSTORE(key=Op.PUSH32[0x0], value=Op.PUSH32[0x0])
        + Op.PUSH32[coinbase]
        + Op.EXP
        + Op.DUP5
        + Op.CALLER
        + Op.SWAP2
        + Op.LOG0(offset=0x6595668352, size=Op.DUP9)
        + Op.SSTORE(key=Op.MLOAD(offset=0x0), value=0x8555),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.SSTORE(
                key=Op.PUSH32[0x0],
                value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
            )
            + Op.SSTORE(key=Op.PUSH32[0x0], value=Op.PUSH32[0x0])
            + Op.PUSH32[coinbase]
            + Op.EXP
            + Op.DUP5
            + Op.CALLER
            + Op.SWAP2
            + Op.LOG0(offset=0x6595668352, size=Op.DUP9)
            + Bytes("6185")
        ),
        gas_limit=100000,
        value=0x55500EE3,
    )

    post = {
        target: Account(storage={}, balance=0, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
