"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest100Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest100Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest100(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x9,
                condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLDATALOAD(offset=0x20),
            )
        ),
        balance=46,
        nonce=0,
        address=coinbase,  # noqa: E501
    )
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.COINBASE
            + Op.TIMESTAMP
            + Op.SSTORE(
                key=Op.PREVRANDAO,
                value=Op.CALLCODE(
                    gas=Op.DUP4,
                    address=Op.TIMESTAMP,
                    value=Op.PREVRANDAO,
                    args_offset=Op.TIMESTAMP,
                    args_size=Op.NUMBER,
                    ret_offset=Op.PREVRANDAO,
                    ret_size=Op.NUMBER,
                ),
            )
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xac7af608fdd0c1e915c85a0dded54637285b93b0"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("42"),
        gas_limit=400000,
        value=100000,
    )

    post = {
        contract: Account(storage={0x20000: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
