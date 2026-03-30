"""
Test_sha3_dejavu.

Ported from:
state_tests/stMemoryTest/sha3_dejavuFiller.json
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
    ["state_tests/stMemoryTest/sha3_dejavuFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_sha3_dejavu(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_sha3_dejavu."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x7DD1D0EC78FE936B0E88F8C21226F51F048579915C7BAFF1C5D7FD84B2139BF1
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=52949672960,
    )

    # Source: raw
    # 0x60FF630FFFFFFF20
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SHA3(offset=0xFFFFFFF, size=0xFF),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xA9B85B894D15D75175CE20CC2D6810154894110C),  # noqa: E501
    )
    pre[sender] = Account(balance=0x271000000000)

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
