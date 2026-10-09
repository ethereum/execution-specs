"""
Test_random_statetest353.

Ported from:
state_tests/stRandom/randomStatetest353Filler.json
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
    ["state_tests/stRandom/randomStatetest353Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest353(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest353."""
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
    # 0x7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7f00000000000000000000000000000000000000000000000000000000000000017f00000000000000000000000000000000000000000000000000000000000000007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f0000000000000000000000000000000000000000000000000000000000000000357fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f0000000000000000000000010000000000000000000000000000000000000000120ba49036880f86529655  # noqa: E501
    target = pre.deploy_contract(
        code=(
            Op.PUSH32[coinbase]
            + Op.PUSH32[0x1]
            + Op.PUSH32[0x0]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Op.SIGNEXTEND(
                Op.SLT(
                    Op.PUSH32[0x10000000000000000000000000000000000000000],
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ),
                Op.CALLDATALOAD(offset=Op.PUSH32[0x0]),
            )
            + Op.LOG4
            + Op.SWAP1
            + Op.CALLDATASIZE
            + Op.DUP9
            + bytes.fromhex("0f86529655")
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[coinbase]
            + Op.PUSH32[0x1]
            + Op.PUSH32[0x0]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ]
            + Op.SIGNEXTEND(
                Op.SLT(
                    Op.PUSH32[0x10000000000000000000000000000000000000000],
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ),
                Op.CALLDATALOAD(offset=Op.PUSH32[0x0]),
            )
            + Op.LOG4
            + Op.SWAP1
            + Op.CALLDATASIZE
            + Op.DUP9
            + Bytes("0f865296")
        ),
        gas_limit=100000,
        value=0x66F823BB,
    )

    post = {
        target: Account(storage={}, balance=0, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
