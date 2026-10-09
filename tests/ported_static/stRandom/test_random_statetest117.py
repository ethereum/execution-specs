"""
Test_random_statetest117.

Ported from:
state_tests/stRandom/randomStatetest117Filler.json

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
    ["state_tests/stRandom/randomStatetest117Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest117(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest117."""
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
    # 0x447f00000000000000000000000000000000000000000000000000000000000000017f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>427f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000100000000000000000000000000000000000000006f8aa4a4980274f18c6158368d4157145560005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PREVRANDAO
        + Op.PUSH32[0x1]
        + Op.PUSH32[coinbase]
        + Op.TIMESTAMP
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0), value=0x8AA4A4980274F18C6158368D41571455
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PREVRANDAO
            + Op.PUSH32[0x1]
            + Op.PUSH32[coinbase]
            + Op.TIMESTAMP
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Bytes("6f8aa4a4980274f18c6158368d415714")
        ),
        value=0x691AC7A4,
    )

    post = {
        target: Account(
            storage={0: 0x8AA4A4980274F18C6158368D41571455},
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
