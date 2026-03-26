"""
test_random_statetest414

Ported from:
state_tests/stRandom2/randomStatetest414Filler.json
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
    ["state_tests/stRandom2/randomStatetest414Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest414(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_random_statetest414"""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = EOA(
        key=0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6251437f0000000000000000000000010000000000000000000000000000000000000000437f000000000000000000000000fffffffffffffffffffffffffffffffffffffffff11460005155
    target = pre.deploy_contract(
        code=Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH3[0x51437f] + Op.STOP * 11 + Op.ADD + Op.STOP * 20 + Op.NUMBER
        + Op.SSTORE(key=Op.MLOAD(offset=0x0), value=Op.EQ(Op.CALL, Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff])),  # noqa: E501
        nonce=0,
        address=Address("0x16000b6b36a20d3093a8b71a9fd8292c8a641002"),  # noqa: E501
    )
    # Source: raw
    # 0x6000355415600957005b60203560003555
    coinbase = pre.deploy_contract(
        code=Op.JUMPI(pc=0x9, condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))))  # noqa: E501
        + Op.STOP + Op.JUMPDEST
        + Op.SSTORE(key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)),  # noqa: E501
        balance=46,
        nonce=0,
        address=Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6251437f0000000000000000000000010000000000000000000000000000000000000000437f000000000000000000000000fffffffffffffffffffffffffffffffffffffffff114"),  # noqa: E501
        gas_limit=100000,
        value=0x40e7cc29,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={}, nonce=0),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
