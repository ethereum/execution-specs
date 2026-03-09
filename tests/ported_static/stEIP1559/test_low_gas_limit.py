"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP1559/lowGasLimitFiller.yml
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
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP1559/lowGasLimitFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, tx_error, expected_post",
    [
        pytest.param(
            90000,
            TransactionException.GAS_ALLOWANCE_EXCEEDED,
            {
                Address("0xef0454d0376d1921b9a83868282725853c293ab5"): Account(
                    storage={0: 24743}
                )
            },
            id="case0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            50000,
            None,
            {
                Address("0xef0454d0376d1921b9a83868282725853c293ab5"): Account(
                    storage={0: 2}
                )
            },
            id="case1",
        ),
        pytest.param(
            25000,
            None,
            {
                Address("0xef0454d0376d1921b9a83868282725853c293ab5"): Account(
                    storage={0: 24743}
                )
            },
            id="case2",
        ),
        pytest.param(
            20000,
            TransactionException.INTRINSIC_GAS_TOO_LOW,
            {
                Address("0xef0454d0376d1921b9a83868282725853c293ab5"): Account(
                    storage={0: 24743}
                )
            },
            id="case3",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_low_gas_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    tx_error: object,
    expected_post: dict,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xDE0C95357363DA5C1C5A73BD7C2781CA5C9FECC1014103B5E1D1E990AE8208EC
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=80000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)
    # Source: Yul
    # {
    #     sstore(0, add(1,1))
    # }
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x2) + Op.STOP,
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xef0454d0376d1921b9a83868282725853c293ab5"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=tx_gas_limit,
        max_fee_per_gas=1000,
        max_priority_fee_per_gas=1000,
        nonce=1,
        error=tx_error,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
