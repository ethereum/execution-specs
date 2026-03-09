"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom2/randomStatetest588Filler.json
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
    ["tests/static/state_tests/stRandom2/randomStatetest588Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest588(
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

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.COINBASE
            + Op.NUMBER
            + Op.PUSH32[0x1]
            + Op.CALLDATACOPY(
                dest_offset=Op.MOD(
                    Op.NUMBER,
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ),
                offset=Op.PUSH32[0x1],
                size=Op.PUSH32[0xC350],
            )
            + Op.MLOAD(offset=0x0)
            + Op.SSTORE
        ),
        nonce=0,
        address=Address("0x2c3d41995b7f3d32e08c6575e2ddaa1ae5cf2067"),  # noqa: E501
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

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff41437f"  # noqa: E501
            "00000000000000000000000000000000000000000000000000000000000000017f000000"  # noqa: E501
            "000000000000000000000000000000000000000000000000000000c3507f000000000000"  # noqa: E501
            "00000000000000000000000000000000000000000000000000017fffffffffffffffffff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffffffffffffff430637"
        ),
        gas_limit=100000,
        value=1725348983,
    )

    post = {
        contract: Account(
            storage={
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF: 1,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
