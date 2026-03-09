"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest9Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest9Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest9(
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
            + Op.PUSH32[0x1]
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[0x1]
            + Op.PUSH32[0x1]
            + Op.PUSH32[0x1]
            + Op.SSTORE(
                key=Op.MLOAD(offset=0x0),
                value=0x757FB845405BF1FF959BA03A9C336B55,
            )
        ),
        nonce=0,
        address=Address("0xe4b1e633c823d5bfde55301aaf1d5ad28816f1ef"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "7f000000000000000000000000000000000000000000000000000000000000c3507f0000"  # noqa: E501
            "0000000000000000000000000000000000000000000000000000000000017f0000000000"  # noqa: E501
            "0000000000000100000000000000000000000000000000000000007fffffffffffffffff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffffffffffffffff7f0000000000000000000000"  # noqa: E501
            "00ffffffffffffffffffffffffffffffffffffffff7f0000000000000000000000000000"  # noqa: E501
            "0000000000000000000000000000000000017f0000000000000000000000000000000000"  # noqa: E501
            "0000000000000000000000000000017f0000000000000000000000000000000000000000"  # noqa: E501
            "0000000000000000000000016f757fb845405bf1ff959ba03a9c336b"
        ),
        gas_limit=100000,
        value=217035801,
    )

    post = {
        contract: Account(storage={0: 0x757FB845405BF1FF959BA03A9C336B55}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
