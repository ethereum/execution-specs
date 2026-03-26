"""
test_random_statetest343

Ported from:
state_tests/stRandom/randomStatetest343Filler.json
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
    ["state_tests/stRandom/randomStatetest343Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest343(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_random_statetest343"""
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
    # 0x7f00000000000000000000000000000000000000000000000000000000000000017f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000000000000000000000000000000000000000c3507f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff1110103741355560005155
    target = pre.deploy_contract(
        code=Op.PUSH32[0x1] + Op.PUSH32[0xc350]
        + Op.CALLDATACOPY(dest_offset=Op.LT(Op.LT(Op.GT(Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff], Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff]), Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff]), Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffff]), offset=Op.PUSH32[0x0], size=Op.PUSH32[0xc350])
        + Op.CALLDATALOAD(offset=Op.COINBASE) + Op.SSTORE + Op.MLOAD(offset=0x0)
        + Op.SSTORE,
        nonce=0,
        address=Address("0x0c6077c4b33cd05c78d87cb0c0186bb869d3c773"),  # noqa: E501
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
        data=bytes.fromhex("7f00000000000000000000000000000000000000000000000000000000000000017f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000000000000000000000000000000000000000c3507f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff111010374135"),  # noqa: E501
        gas_limit=100000,
        value=0x4d914770,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
                storage={
            0: 50000,
            0x7f000000000000000000000000000000000000000000000000000000000000: 1,
        },
                nonce=0,
            ),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
