"""
Test_random_statetest415.

Ported from:
state_tests/stRandom2/randomStatetest415Filler.json
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
    ["state_tests/stRandom2/randomStatetest415Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest415(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest415."""
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
    # 0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff437f000000000000000000000000000000000000000000000000000000000000000142427f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>357f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff62010a8c8794a17e8ea4f260005155  # noqa: E501
    target = pre.deploy_contract(
        code=(
            Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Op.NUMBER
            + Op.PUSH32[0x1]
            + Op.TIMESTAMP * 2
            + Op.CALLDATALOAD(offset=Op.PUSH32[coinbase])
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH3[0x10A8C]
            + Op.DUP8
            + Op.SWAP5
            + Op.LOG1
            + bytes.fromhex("7e8ea4f260005155")
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
            + Op.NUMBER
            + Op.PUSH32[0x1]
            + Op.TIMESTAMP * 2
            + Op.CALLDATALOAD(offset=Op.PUSH32[coinbase])
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH3[0x10A8C]
            + Op.DUP8
            + Op.SWAP5
            + Op.LOG1
            + Bytes("7e8ea4f2")
        ),
        gas_limit=600000,
        value=0x49A12105,
    )

    post = {
        target: Account(storage={}, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
