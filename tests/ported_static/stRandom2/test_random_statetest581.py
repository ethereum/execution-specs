"""
Test_random_statetest581.

Ported from:
state_tests/stRandom2/randomStatetest581Filler.json
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
    ["state_tests/stRandom2/randomStatetest581Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest581(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest581."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
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
    # 0x7f00000000000000000000000000000000000000000000000000000000000000017f0000000000000000000000000000000000000000000000000000000000000001037f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff44920907ff7e7d701260005155  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex(
            "7f00000000000000000000000000000000000000000000000000000000000000017f0000000000000000000000000000000000000000000000000000000000000001037f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff44920907ff7e7d701260005155"  # noqa: E501
        ),
        nonce=0,
        address=Address("0x2e41249a09bb2414d41641bd9cd9a15393d41e76"),  # noqa: E501
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
        address=Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex(
            "7f00000000000000000000000000000000000000000000000000000000000000017f0000000000000000000000000000000000000000000000000000000000000001037f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff44920907ff7e7d7012"  # noqa: E501
        ),
        gas_limit=100000,
        value=0x5D315A13,
        gas_price=10,
    )

    post = {
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
        Address("0xffffffffffffffffffffffffffffffffffffffff"): Account(
            storage={}, code=b"", nonce=0
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
