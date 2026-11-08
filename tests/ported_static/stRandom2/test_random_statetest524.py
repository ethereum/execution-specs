"""
Test_random_statetest524.

Ported from:
state_tests/stRandom2/randomStatetest524Filler.json
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
    ["state_tests/stRandom2/randomStatetest524Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest524(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest524."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x457ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe427f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff357f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000000000000000000000000000000000000000000034208a340a9e5560005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.GASLIMIT
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.TIMESTAMP
        + Op.CALLDATALOAD(
            offset=Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        )
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.PUSH32[0x0]
        + Op.SHA3(offset=Op.CALLVALUE, size=Op.PUSH32[0x0])
        + Op.EXP(Op.CALLVALUE, Op.DUP11)
        + Op.SWAP15
        + Op.SSTORE
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
            "457ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe427f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff357f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000000000000000000000000000000000000000000034208a340a9e"  # noqa: E501
        ),
        gas_limit=100000,
        value=0x754EB077,
    )

    post = {
        target: Account(storage={}, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
