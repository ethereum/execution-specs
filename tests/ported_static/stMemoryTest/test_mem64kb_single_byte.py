"""
test_mem64kb_single_byte

Ported from:
state_tests/stMemoryTest/mem64kb_singleByteFiller.json
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
    ["state_tests/stMemoryTest/mem64kb_singleByteFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_mem64kb_single_byte(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_mem64kb_single_byte"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x834185262e53584684bf2b72c64e510013c235d0f45e462db65900455df45a35
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=42949672960,
    )

    # Source: lll
    # { (MSTORE8 63999 42) [[ 0 ]] (MSIZE) }
    target = pre.deploy_contract(
        code=Op.MSTORE8(offset=0xf9ff, value=0x2a)
        + Op.SSTORE(key=0x0, value=Op.MSIZE) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x6c0cf9e7fba0563117dbf01f9126777d60bc54b4"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=100000,
        value=10,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={0: 64000}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
