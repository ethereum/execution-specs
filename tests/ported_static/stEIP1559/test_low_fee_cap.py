"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/stEIP1559/lowFeeCapFiller.yml
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
    TransactionException,
    AccessList,
    Hash,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP1559/lowFeeCapFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.exception_test
@pytest.mark.pre_alloc_mutable
def test_low_fee_cap(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xde0c95357363da5c1c5a73bd7c2781ca5c9fecc1014103b5e1d1e990ae8208ec
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=1000,
        gas_limit=71794957647893862,
    )

    # Source: yul
    # berlin {
    #     sstore(0, add(1,1))
    # }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x2) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xd71b14c239fc39327f25764dd784c85ef0285fda"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("00"),
        gas_limit=400000,
        value=0x186a0,
        max_fee_per_gas=999,
        max_priority_fee_per_gas=100,
        nonce=1,
        error=TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
