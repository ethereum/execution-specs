"""
Test_random_statetest484.

Ported from:
state_tests/stRandom2/randomStatetest484Filler.json
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
    ["state_tests/stRandom2/randomStatetest484Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest484(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest484."""
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
    # 0x7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff35427ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>595584a2558493a25b5a6a60005155  # noqa: E501
    target = pre.deploy_contract(
        code=(
            Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[0x0]
            + Op.CALLDATALOAD(
                offset=Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            )
            + Op.TIMESTAMP
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Op.PUSH32[0xC350]
            + Op.SSTORE(key=Op.MSIZE, value=Op.PUSH32[coinbase])
            + Op.DUP5
            + Op.LOG2
            + Op.SSTORE
            + Op.DUP5
            + Op.SWAP4
            + Op.LOG2
            + Op.JUMPDEST
            + Op.GAS
            + bytes.fromhex("6a60005155")
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[0x0]
            + Op.CALLDATALOAD(
                offset=Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            )
            + Op.TIMESTAMP
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Op.PUSH32[0xC350]
            + Op.SSTORE(key=Op.MSIZE, value=Op.PUSH32[coinbase])
            + Op.DUP5
            + Op.LOG2
            + Op.SSTORE
            + Op.DUP5
            + Op.SWAP4
            + Op.LOG2
            + Op.JUMPDEST
            + Op.GAS
            + Bytes("6a")
        ),
        gas_limit=500000,
        value=0x1BBD5E60,
    )

    post = {
        target: Account(storage={}, balance=0, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
