"""
Test_random_statetest321.

Ported from:
state_tests/stRandom/randomStatetest321Filler.json
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
    ["state_tests/stRandom/randomStatetest321Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest321(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest321."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x7f00000000000000000000000000000000000000000000000000000000000000017f00000000000000000000000100000000000000000000000000000000000000007f00000000000000000000000000000000000000000000000000000000000000006a7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff033a06869867986202413a537c60005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[0x1]
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH32[0x0]
        + Op.PUSH11[0x7F00000000000000000000]
        + Op.STOP * 2
        + Op.SELFDESTRUCT * 20
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        + Op.MOD(
            Op.GASPRICE,
            Op.SUB(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF],
            ),
        )
        + Op.DUP7
        + Op.SWAP9
        + Op.PUSH8[0x986202413A537C60]
        + Op.STOP
        + Op.MLOAD
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
            "7f00000000000000000000000000000000000000000000000000000000000000017f00000000000000000000000100000000000000000000000000000000000000007f00000000000000000000000000000000000000000000000000000000000000006a7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff033a06869867986202413a537c"  # noqa: E501
        ),
        gas_limit=100000,
        value=0x63349441,
    )

    post = {
        target: Account(storage={}, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
