"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom2/randomStatetest626Filler.json
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
    ["tests/static/state_tests/stRandom2/randomStatetest626Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest626(
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
            + Op.REVERT(
                offset=Op.DELEGATECALL(
                    gas=Op.PUSH32[0xC350],
                    address=Op.PUSH32[
                        0x4F3F701464972E74606D6EA82D4D3080599A0E79
                    ],
                    args_offset=Op.PUSH32[0x1],
                    args_size=Op.PUSH32[0x0],
                    ret_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    ret_size=Op.PUSH32[0x1],
                ),
                size=Op.PUSH32[0xC350],
            )
            + Op.SWAP5
            + Op.MOD(Op.DUP16, Op.SDIV)
            + Op.LOG2
            + Op.SSTORE
        ),
        nonce=0,
        address=Address("0xf55f25b074cbf8502ed5a9d1e2aab4d351b67af2"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "7f00000000000000000000000100000000000000000000000000000000000000007f0000"  # noqa: E501
            "00000000000000000000000000000000000000000000000000000000c3507f0000000000"  # noqa: E501
            "0000000000000000000000000000000000000000000000000000017fffffffffffffffff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffffffffffffffff7f0000000000000000000000"  # noqa: E501
            "0000000000000000000000000000000000000000007f0000000000000000000000000000"  # noqa: E501
            "0000000000000000000000000000000000017f0000000000000000000000004f3f701464"  # noqa: E501
            "972e74606d6ea82d4d3080599a0e797f0000000000000000000000000000000000000000"  # noqa: E501
            "00000000000000000000c350f4fd94058f06a2"
        ),
        gas_limit=100000,
        value=1996511098,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
