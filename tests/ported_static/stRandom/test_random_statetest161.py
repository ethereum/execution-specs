"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest161Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest161Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest161(
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
            Op.PUSH32[0x1]
            + Op.PUSH32[0xC350]
            + Op.NUMBER
            + Op.PUSH32[0x0]
            + Op.PUSH32[0x1]
            + Op.COINBASE
            + Op.SSTORE(
                key=Op.MLOAD(offset=0x0),
                value=0x458A458076526052650A418C9B40863C,
            )
        ),
        nonce=0,
        address=Address("0x92dc542f486da68eafa3db73723551927d3fdba7"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "7f00000000000000000000000000000000000000000000000000000000000000017f0000"  # noqa: E501
            "00000000000000000000000000000000000000000000000000000000c350437f00000000"  # noqa: E501
            "000000000000000000000000000000000000000000000000000000007f00000000000000"  # noqa: E501
            "00000000000000000000000000000000000000000000000001416f458a45807652605265"  # noqa: E501
            "0a418c9b40863c"
        ),
        gas_limit=100000,
        value=757362865,
    )

    post = {
        contract: Account(storage={0: 0x458A458076526052650A418C9B40863C}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
