"""
Test_random_statetest409.

Ported from:
state_tests/stRandom2/randomStatetest409Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    Fork,
)
from execution_testing.vm import Op

from execution_testing.forks import Amsterdam

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom2/randomStatetest409Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest409(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_random_statetest409."""
    coinbase = Address(0x4F3F701464972E74606D6EA82D4D3080599A0E79)
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

    # Source: raw
    # 0x5b7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000100000000000000000000000000000000000000007f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000001000000000000000000000000000000000000000009ff511287868833063aa3579d8e585560005155  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH32[0x4F3F701464972E74606D6EA82D4D3080599A0E79]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        + Op.SELFDESTRUCT(
            address=Op.MULMOD(
                Op.PUSH32[0x10000000000000000000000000000000000000000],
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
        )
        + Op.MLOAD
        + Op.LOG3(
            offset=Op.GASPRICE,
            size=Op.MOD(Op.CALLER, Op.DUP9),
            topic_1=Op.DUP7,
            topic_2=Op.DUP8,
            topic_3=Op.SLT,
        )
        + Op.JUMPI
        + Op.SWAP14
        + Op.SSTORE(key=Op.PC, value=Op.DUP15)
        + Op.MLOAD(offset=0x0)
        + Op.SSTORE,
        nonce=0,
        address=Address(0x68076CF2C7430BB5E7CBAA157DEBE1C7CC9B30AE),  # noqa: E501
    )
    # Source: raw
    # 0x6000355415600957005b60203560003555
    coinbase = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x9,
            condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
        )
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(
            key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)
        ),
        balance=46,
        nonce=0,
        address=Address(0x4F3F701464972E74606D6EA82D4D3080599A0E79),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "5b7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000100000000000000000000000000000000000000007f0000000000000000000000004f3f701464972e74606d6ea82d4d3080599a0e797fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000001000000000000000000000000000000000000000009ff511287868833063aa3579d8e58"  # noqa: E501
        ),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
        value=0x41028C83,
    )

    post = {
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
        Address(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF): Account(
            storage={}, code=b"", balance=0x41028C83, nonce=0
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
