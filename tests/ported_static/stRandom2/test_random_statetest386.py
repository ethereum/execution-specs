"""
Test_random_statetest386.

Ported from:
state_tests/stRandom2/randomStatetest386Filler.json


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
    ["state_tests/stRandom2/randomStatetest386Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest386(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest386."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x7f00000000000000000000000000000000000000000000000000000000000000007f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff047f000000000000000000000000000000000000000000000000000000000000000105133641010b811160005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[0x0] * 2
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0),
            value=Op.GT(
                Op.DUP2,
                Op.SIGNEXTEND(
                    Op.ADD(Op.COINBASE, Op.CALLDATASIZE),
                    Op.SGT(
                        Op.SDIV(
                            Op.PUSH32[0x1],
                            Op.DIV(
                                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                            ),
                        ),
                        Op.PUSH32[0x0],
                    ),
                ),
            ),
        ),
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
            "7f00000000000000000000000000000000000000000000000000000000000000007f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff047f000000000000000000000000000000000000000000000000000000000000000105133641010b8111"  # noqa: E501
        ),
        value=0x19D7AC44,
    )

    post = {
        target: Account(storage={0: 1}, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
