"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest383Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest383Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest383(
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
            "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f0000"  # noqa: E501
            "000000000000000000004f3f701464972e74606d6ea82d4d3080599a0e797fffffffffff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffff7f0000000000000000"  # noqa: E501
            "00000000ffffffffffffffffffffffffffffffffffffffff7f0000000000000000000000"  # noqa: E501
            "004f3f701464972e74606d6ea82d4d3080599a0e797f000000000000000000000000ffff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffff"  # noqa: E501
            "ffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffff"  # noqa: E501
            "ffffffffffffffffffffffff09150255436c75107e"
        ),
        nonce=0,
        address=Address("0x9306b5e9e12f8e3524cb929c05e3f817fd403029"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f0000"  # noqa: E501
            "000000000000000000004f3f701464972e74606d6ea82d4d3080599a0e797fffffffffff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffff7f0000000000000000"  # noqa: E501
            "00000000ffffffffffffffffffffffffffffffffffffffff7f0000000000000000000000"  # noqa: E501
            "004f3f701464972e74606d6ea82d4d3080599a0e797f000000000000000000000000ffff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffff"  # noqa: E501
            "ffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffff"  # noqa: E501
            "ffffffffffffffffffffffff09150255436c75107e"
        ),
        gas_limit=100000,
        value=1668923511,
    )

    post = {
        Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"): Account(
            storage={
                0x945304EB96065B2A98B57A48A06AE28D285A71B5: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            },
            nonce=0,
            balance=0x6379C077,
        ),
        Address("0x945304eb96065b2a98b57a48a06ae28d285a71b5"): Account(
            storage={},
            nonce=0,
        ),
        Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b"): Account(
            storage={},
            nonce=1,
            code=b"",
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
