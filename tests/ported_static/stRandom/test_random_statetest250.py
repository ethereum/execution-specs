"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest250Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest250Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest250(
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
            Op.SSTORE
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE  # noqa: E501
            ]
            + Op.PUSH32[0x1]
            + Op.PUSH32[0xC350]
            + Op.PUSH32[0x4F3F701464972E74606D6EA82D4D3080599A0E79]
            + Op.PUSH3[0x7F0000]
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.ADD
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.STOP
            + Op.MUL(
                0x328B186E166407917C7AF1,
                Op.PUSH32[0x4F3F701464972E74606D6EA82D4D3080599A0E79],
            )
            + Op.SWAP3
            + Op.POP
            + Op.MLOAD(offset=0x0)
            + Op.SSTORE
        ),
        nonce=0,
        address=Address("0x089927daf7e20b167e29c7dc686d18639371e6bf"),  # noqa: E501
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
            "557ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f00"  # noqa: E501
            "000000000000000000000000000000000000000000000000000000000000017f00000000"  # noqa: E501
            "0000000000000000000000000000000000000000000000000000c3507f00000000000000"  # noqa: E501
            "00000000004f3f701464972e74606d6ea82d4d3080599a0e79627f000000000000000000"  # noqa: E501
            "00000100000000000000000000000000000000000000007f000000000000000000000000"  # noqa: E501
            "4f3f701464972e74606d6ea82d4d3080599a0e796a328b186e166407917c7af1029250"  # noqa: E501
        ),
        gas_limit=100000,
        value=1535680761,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
