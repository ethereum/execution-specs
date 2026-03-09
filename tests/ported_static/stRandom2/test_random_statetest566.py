"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom2/randomStatetest566Filler.json
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
    ["tests/static/state_tests/stRandom2/randomStatetest566Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest566(
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
            Op.SWAP11
            + Op.GT(Op.PUSH32[0x0], Op.PUSH32[0xC350])
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.TIMESTAMP
            + Op.PUSH32[0x4F3F701464972E74606D6EA82D4D3080599A0E79]
            + Op.SWAP4
            + Op.SWAP7
            + Op.JUMPI(pc=Op.ORIGIN, condition=Op.CALLER)
            + Op.DUP7
            + Op.PUSH6[0x734360005155]
        ),
        nonce=0,
        address=Address("0xe8fda25222733f9c226c2e5b6dca729eb71076fd"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "9a7f000000000000000000000000000000000000000000000000000000000000c3507f00"  # noqa: E501
            "00000000000000000000000000000000000000000000000000000000000000117f000000"  # noqa: E501
            "00000000000000000100000000000000000000000000000000000000007fffffffffffff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffffffffffffffffffff427f0000000000000000"  # noqa: E501
            "000000004f3f701464972e74606d6ea82d4d3080599a0e79939633325786657343"  # noqa: E501
        ),
        gas_limit=100000,
        value=565778672,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
