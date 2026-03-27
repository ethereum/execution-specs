"""
Test_random_statetest199.

Ported from:
state_tests/stRandom/randomStatetest199Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom/randomStatetest199Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest199(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest199."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x30424543074242413155
    target = pre.deploy_contract(  # noqa: F841
        code=Op.ADDRESS
        + Op.TIMESTAMP
        + Op.SMOD(Op.NUMBER, Op.GASLIMIT)
        + Op.TIMESTAMP
        + Op.SSTORE(key=Op.BALANCE(address=Op.COINBASE), value=Op.TIMESTAMP),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x961ce95e83ad7816d5fec439ea9847ca3a5543c5"),  # noqa: E501
    )
    # Source: raw
    # 0x6000355415600957005b60203560003555
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
        nonce=0,
        address=Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("42"),
        gas_limit=400000,
        value=0x186A0,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
            storage={46: 1000},
            balance=0xDE0B6B3A76586A0,
            nonce=0,
        ),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
