"""
Test_random_statetest313.

Ported from:
state_tests/stRandom/randomStatetest313Filler.json
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
    ["state_tests/stRandom/randomStatetest313Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest313(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest313."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x0b7f00000000000000000000000000000000000000000000000000000000000000013c7f000000000000000000000000000000000000000000000000000000000000c350a345457fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff8287a3208c8c5a60005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SIGNEXTEND
        + Op.PUSH32[0x1]
        + Op.EXTCODECOPY
        + Op.PUSH32[0xC350]
        + Op.LOG3
        + Op.LOG3(
            offset=Op.DUP8,
            size=Op.DUP3,
            topic_1=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            topic_2=Op.GASLIMIT,
            topic_3=Op.GASLIMIT,
        )
        + Op.SHA3
        + Op.DUP13 * 2
        + Op.SSTORE(key=Op.MLOAD(offset=0x0), value=Op.GAS),
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
            "0b7f00000000000000000000000000000000000000000000000000000000000000013c7f000000000000000000000000000000000000000000000000000000000000c350a345457fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff8287a3208c8c5a"  # noqa: E501
        ),
        gas_limit=100000,
        value=0x3159E0F9,
    )

    post = {
        target: Account(storage={}, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
