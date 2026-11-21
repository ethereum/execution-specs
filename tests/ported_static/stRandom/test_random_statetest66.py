"""
Test_random_statetest66.

Ported from:
state_tests/stRandom/randomStatetest66Filler.json

@manually-enhanced: Do not overwrite. Explicit gas values removed.
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
    ["state_tests/stRandom/randomStatetest66Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest66(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest66."""
    sender = pre.fund_eoa()

    coinbase = pre.deploy_contract(  # noqa: F841
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
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.GASLIMIT
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        + Op.COINBASE
        + Op.SSTORE(
            key=Op.PUSH32[0x10000000000000000000000000000000000000000],
            value=Op.MULMOD(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                Op.PUSH32[0x945304EB96065B2A98B57A48A06AE28D285A71B5],
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            ),
        ),
    )

    env = Environment(
        fee_recipient=coinbase,
        prev_randao=0x20000,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(
            "457fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff417fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe097f0000000000000000000000010000000000000000000000000000000000000000"  # noqa: E501
        ),
        value=0x2F5660CE,
    )

    post = {
        contract_0: Account(
            storage={
                0x10000000000000000000000000000000000000000: 0xFFFFFFFFFFFFFFFFFFFFFFFF6BACFB1469F9A4D5674A85B75F951D72D7A58E4A,  # noqa: E501
            },
        ),
        coinbase: Account(storage={}),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
