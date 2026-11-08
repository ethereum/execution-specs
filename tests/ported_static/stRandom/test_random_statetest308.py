"""
Test_random_statetest308.

Ported from:
state_tests/stRandom/randomStatetest308Filler.json
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
    ["state_tests/stRandom/randomStatetest308Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
def test_random_statetest308(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest308."""
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
    # 0x7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b5357f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe427f000000000000000000000000000000000000000000000000000000000000c3507f0000000000000000000000010000000000000000000000000000000000000000085a01096630f38c9a60005155  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.PUSH32[coinbase]
        + Op.CALLDATALOAD(offset=Op.PUSH32[coinbase])
        + Op.SSTORE(
            key=0x30F38C9A600051,
            value=Op.MULMOD(
                Op.ADD(
                    Op.GAS,
                    Op.ADDMOD(
                        Op.PUSH32[0x10000000000000000000000000000000000000000],
                        Op.PUSH32[0xC350],
                        Op.TIMESTAMP,
                    ),
                ),
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF],
            ),
        ),
    )

    env = Environment(
        fee_recipient=coinbase, prev_randao=0x20000, gas_limit=HIGH_GAS_LIMIT
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=(
            Op.PUSH32[coinbase]
            + Op.CALLDATALOAD(offset=Op.PUSH32[coinbase])
            + Op.MULMOD(
                Op.ADD(
                    Op.GAS,
                    Op.ADDMOD(
                        Op.PUSH32[0x10000000000000000000000000000000000000000],
                        Op.PUSH32[0xC350],
                        Op.TIMESTAMP,
                    ),
                ),
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
                Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF],
            )
            + Bytes("6630f38c9a")
        ),
        gas_limit=1559407972,
        value=0x1695F3D,
    )

    post = {
        contract_0: Account(
            storage={
                0x30F38C9A600051: 0x5CF25686FFFFFFFFFFFFFFFF461B52F2,
            },
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
