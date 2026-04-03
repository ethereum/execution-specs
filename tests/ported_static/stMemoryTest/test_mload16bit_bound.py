"""
Test_mload16bit_bound.

Ported from:
state_tests/stMemoryTest/mload16bitBoundFiller.json
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
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stMemoryTest/mload16bitBoundFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_mload16bit_bound(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_mload16bit_bound."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xA9DF11BD92FC8535FFCA3AE0A2133C80D5F4ECC5D31D100B94FF03E63F7E74FF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=17592320524892,
    )

    # Source: lll
    # { [[ 1 ]] (MLOAD 65536) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x10000)) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x85EAA01AC6288C06360D431D62CD865C92B74A28),  # noqa: E501
    )
    pre[sender] = Account(balance=0xA00050281798)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
        value=10,
    )

    post = {
        target: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
