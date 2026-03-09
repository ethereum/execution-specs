"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest323Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest323Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest323(
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
        code=bytes.fromhex(
            "6f7f00000000000000000000000000000000000000000000000000000000000000007f00"  # noqa: E501
            "0000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000"  # noqa: E501
            "00000000000000004f3f701464972e74606d6ea82d4d3080599a0e797fffffffffffffff"  # noqa: E501
            "fffffffffffffffffffffffffffffffffffffffffffffffffe74977f0000000000000000"  # noqa: E501
            "00000000000000000000000000000000000000000000c3506f6b79361811363920600051"  # noqa: E501
            "55"
        ),
        nonce=0,
        address=Address("0x70da9b48406e4b67e6cc0458d7376116d08eb806"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "6f7f00000000000000000000000000000000000000000000000000000000000000007f00"  # noqa: E501
            "0000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000"  # noqa: E501
            "00000000000000004f3f701464972e74606d6ea82d4d3080599a0e797fffffffffffffff"  # noqa: E501
            "fffffffffffffffffffffffffffffffffffffffffffffffffe74977f0000000000000000"  # noqa: E501
            "00000000000000000000000000000000000000000000c3506f6b79361811363920"  # noqa: E501
        ),
        gas_limit=100000,
        value=1955628831,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRandom/randomStatetest323Filler.json"],
)
@pytest.mark.valid_from("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest323_from_prague(
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
        code=bytes.fromhex(
            "6f7f00000000000000000000000000000000000000000000000000000000000000007f00"  # noqa: E501
            "0000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000"  # noqa: E501
            "00000000000000004f3f701464972e74606d6ea82d4d3080599a0e797fffffffffffffff"  # noqa: E501
            "fffffffffffffffffffffffffffffffffffffffffffffffffe74977f0000000000000000"  # noqa: E501
            "00000000000000000000000000000000000000000000c3506f6b79361811363920600051"  # noqa: E501
            "55"
        ),
        nonce=0,
        address=Address("0x70da9b48406e4b67e6cc0458d7376116d08eb806"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "6f7f00000000000000000000000000000000000000000000000000000000000000007f00"  # noqa: E501
            "0000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000"  # noqa: E501
            "00000000000000004f3f701464972e74606d6ea82d4d3080599a0e797fffffffffffffff"  # noqa: E501
            "fffffffffffffffffffffffffffffffffffffffffffffffffe74977f0000000000000000"  # noqa: E501
            "00000000000000000000000000000000000000000000c3506f6b79361811363920"  # noqa: E501
        ),
        gas_limit=100000,
        value=1955628831,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
