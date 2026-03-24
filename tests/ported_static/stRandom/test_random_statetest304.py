"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest304Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest304Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest304(
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
            Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.LOG2
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.AND
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE  # noqa: E501
            ]
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.SSTORE(
                key=Op.CALL,
                value=Op.SIGNEXTEND(
                    Op.SMOD(Op.ADDRESS, Op.SLOAD(key=Op.DUP13)),
                    Op.SIGNEXTEND(
                        Op.SMOD(
                            Op.TIMESTAMP,
                            Op.PUSH32[
                                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                            ],
                        ),
                        Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF],
                    ),
                ),
            )
            + Op.MLOAD(offset=0x0)
            + Op.SSTORE
        ),
        nonce=0,
        address=Address("0xeed16ab98d10ee33a19828f9fd044b86553a6f06"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "7f0000000000000000000000010000000000000000000000000000000000000000a27f00"  # noqa: E501
            "0000000000000000000000ffffffffffffffffffffffffffffffffffffffff167fffffff"  # noqa: E501
            "fffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000"  # noqa: E501
            "00000000000100000000000000000000000000000000000000007f000000000000000000"  # noqa: E501
            "000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffffffff42070b8c5430070bf1"
        ),
        gas_limit=100000,
        value=691881103,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
