"""
Create a name registrator contract from a creation transaction.

Ported from:
state_tests/stTransitionTest/createNameRegistratorPerTxsBeforeFiller.json
state_tests/stTransitionTest/createNameRegistratorPerTxsAtFiller.json
state_tests/stTransitionTest/createNameRegistratorPerTxsAfterFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stTransitionTest/createNameRegistratorPerTxsBeforeFiller.json",  # noqa: E501
        "state_tests/stTransitionTest/createNameRegistratorPerTxsAtFiller.json",  # noqa: E501
        "state_tests/stTransitionTest/createNameRegistratorPerTxsAfterFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_create_name_registrator_per_txs(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Create a name registrator contract from a creation transaction."""
    sender = pre.fund_eoa()
    tx_value = 0x186A0

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x10]
        + Op.CODECOPY(dest_offset=0x0, offset=0xC, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP
        + Op.JUMPI(
            pc=0x9,
            condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
        )
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(
            key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)
        ),
        value=tx_value,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(
            storage={1: 1},
            code=bytes.fromhex("396000f3006000355415600957005b60"),
            balance=tx_value,
            nonce=1,
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
