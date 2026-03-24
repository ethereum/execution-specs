"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest135Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest135Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest135(
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
            Op.PUSH32[0xC350]
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.COINBASE
            + Op.SSTORE(
                key=Op.DIV(
                    Op.DUP8,
                    Op.AND(
                        0x3192186630,
                        Op.SIGNEXTEND(
                            Op.GAS,
                            Op.SMOD(
                                Op.CREATE(
                                    value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                                    offset=Op.PUSH32[
                                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
                                    ],
                                    size=Op.PUSH32[0x0],
                                ),
                                Op.PUSH32[
                                    0x4F3F701464972E74606D6EA82D4D3080599A0E79
                                ],
                            ),
                        ),
                    ),
                ),
                value=Op.PUSH32[0x0],
            )
        ),
        nonce=0,
        address=Address("0x8be71dfba7b6d76d26a281635b0d1a85d947c1e5"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "7f000000000000000000000000000000000000000000000000000000000000c3507f0000"  # noqa: E501
            "000000000000000000010000000000000000000000000000000000000000417f00000000"  # noqa: E501
            "000000000000000000000000000000000000000000000000000000007f00000000000000"  # noqa: E501
            "00000000004f3f701464972e74606d6ea82d4d3080599a0e797f00000000000000000000"  # noqa: E501
            "000000000000000000000000000000000000000000007f000000000000000000000000ff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffff"  # noqa: E501
            "fffffffffffffffffffffffffffffffff0075a0b643192186630168704"
        ),
        gas_limit=100000,
        value=1650167023,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
