"""
Ported from:
tests/static/state_tests/stTransactionTest/ContractStoreClearsOOGFiller.json

contract code:
    push1 0x00
    push1 0x00
    sstore
    push1 0x00
    push1 0x01
    sstore
    push1 0x00
    push1 0x02
    sstore
    push1 0x00
    push1 0x03
    sstore
    push1 0x00
    push1 0x04
    sstore
    push1 0x00
    push1 0x05
    sstore
    push1 0x00
    push1 0x06
    ... (11 more instructions)
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stTransactionTest/ContractStoreClearsOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_contract_store_clears_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0xdf2e264abeec114532b73774cfa1994aed66a9f6")
    contract = Address("0xc9c8ce4628bda9f8bc4a2caaebb3616f83c4305d")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x5] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x6]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x7] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x8] + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x9] + Op.SSTORE
        + Op.STOP
    ),
        storage={0x0: 0xc, 0x1: 0xc, 0x2: 0xc, 0x3: 0xc, 0x4: 0xc, 0x5: 0xc, 0x6: 0xc, 0x7: 0xc, 0x8: 0xc, 0x9: 0xc},
    )
    pre[sender] = Account(balance=0x1c9c380, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x2b75d0c814eb07c075fccbdd9a036faf651d9c46d7477d6c4f30772cfca90d38"
        ),
        to=contract,
        data=b"",
        gas_limit=23000,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
