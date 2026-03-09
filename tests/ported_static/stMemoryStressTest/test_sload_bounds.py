"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemoryStressTest/SLOAD_BoundsFiller.json
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
    ["tests/static/state_tests/stMemoryStressTest/SLOAD_BoundsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        150000,
        16777216,
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_sload_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xFE5BE118AD5955E30E0FFC4E1F1BBDCAA7F5A67CB1426C4AC19E32C80ECCDC06
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: LLL
    # { (SLOAD 0) (SLOAD 0xffffffff) (SLOAD 0xffffffffffffffff) (SLOAD 0xffffffffffffffffffffffffffffffff) (SLOAD 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(Op.SLOAD(key=0x0))
            + Op.POP(Op.SLOAD(key=0xFFFFFFFF))
            + Op.POP(Op.SLOAD(key=0xFFFFFFFFFFFFFFFF))
            + Op.POP(Op.SLOAD(key=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF))
            + Op.SLOAD(
                key=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1b71c198ea09541afb8301905a0a80d026ebfa17"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x7FFFFFFFFFFFFFFFFFF)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=tx_gas_limit,
        value=1,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
