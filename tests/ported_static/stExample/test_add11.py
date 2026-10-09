"""
A test for (add 1 1) opcode result.

Ported from:
state_tests/stExample/add11Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
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
    ["state_tests/stExample/add11Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_add11(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A test for (add 1 1) opcode result."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: hex
    # 0x
    coinbase = pre.deploy_contract(
        code="",
        nonce=1,
    )
    # Source: lll
    # { [[0]] (ADD 1 1) }
    contract_0_code = Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1)) + Op.STOP
    contract_0 = pre.deploy_contract(
        code=contract_0_code,
        balance=0xDE0B6B3A7640000,
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=400000,
        value=0x186A0,
    )

    post = {
        contract_0: Account(
            storage={0: 2},
            code=contract_0_code,
        ),
        coinbase: Account(nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
        Address(
            0xE94F5374FCE5EDBC8E2A8697C15331677E6EBF0B
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
