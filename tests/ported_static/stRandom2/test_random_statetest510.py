"""
Test_random_statetest510.

Ported from:
state_tests/stRandom2/randomStatetest510Filler.json
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

from tests.ported_static.constants import HIGH_GAS_LIMIT

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom2/randomStatetest510Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
def test_random_statetest510(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest510."""
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
    # 0x7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000017f00000000000000000000000100000000000000000000000000000000000000007f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>447f00000000000000000000000000000000000000000000000000000000000000005a456ff23a88535564545969f162615b93325560005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.PUSH32[0x1]
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH32[coinbase]
        + Op.PREVRANDAO
        + Op.PUSH32[0x0]
        + Op.GAS
        + Op.GASLIMIT
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0), value=0xF23A88535564545969F162615B933255
        ),
    )

    env = Environment(
        fee_recipient=coinbase, prev_randao=0x20000, gas_limit=HIGH_GAS_LIMIT
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[0x1]
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.PUSH32[coinbase]
            + Op.PREVRANDAO
            + Op.PUSH32[0x0]
            + Op.GAS
            + Op.GASLIMIT
            + Bytes("6ff23a88535564545969f162615b9332")
        ),
        gas_limit=1442721045,
        value=0x720BA13A,
    )

    post = {
        target: Account(
            storage={0: 0xF23A88535564545969F162615B933255},
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
