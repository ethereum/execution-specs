"""
Test_random_statetest418.

Ported from:
state_tests/stRandom2/randomStatetest418Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

from tests.ported_static.constants import HIGH_GAS_LIMIT

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom2/randomStatetest418Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
def test_random_statetest418(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest418."""
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
    # 0x7f0000000000000000000000000000000000000000000000000000000000000000437f00000000000000000000000000000000000000000000000000000000000000017f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7f000000000000000000000000000000000000000000000000000000000000c3507f0000000000000000000000000000000000000000000000000000000000000000417fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff12a36234970658a03160005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[0x0]
        + Op.NUMBER
        + Op.LOG3(
            offset=Op.SLT(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                Op.COINBASE,
            ),
            size=Op.PUSH32[0x0],
            topic_1=Op.PUSH32[0xC350],
            topic_2=Op.PUSH32[coinbase],
            topic_3=Op.PUSH32[0x1],
        )
        + Op.LOG0(offset=Op.PC, size=0x349706)
        + Op.SSTORE(key=Op.MLOAD(offset=0x0), value=Op.BALANCE),
    )

    env = Environment(
        fee_recipient=coinbase, prev_randao=0x20000, gas_limit=HIGH_GAS_LIMIT
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[0x0]
            + Op.NUMBER
            + Op.LOG3(
                offset=Op.SLT(
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    Op.COINBASE,
                ),
                size=Op.PUSH32[0x0],
                topic_1=Op.PUSH32[0xC350],
                topic_2=Op.PUSH32[coinbase],
                topic_3=Op.PUSH32[0x1],
            )
            + Op.LOG0(offset=Op.PC, size=0x349706)
            + Op.BALANCE
        ),
        gas_limit=392462029,
        value=0x65A87A48,
    )

    post = {
        target: Account(storage={}, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
