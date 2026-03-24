"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemoryStressTest/SSTORE_BoundsFiller.json
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
    ["tests/static/state_tests/stMemoryStressTest/SSTORE_BoundsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, expected_post",
    [
        (150000, {}),
        (
            16777216,
            {
                Address("0x1f2aee312c3c47bdeb27ff5275fddb33c543e394"): Account(
                    storage={
                        32: 0xFFFFFFFF,
                        64: 0xFFFFFFFFFFFFFFFF,
                        128: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                        256: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                        0xFFFFFFFF: 1,
                        0xFFFFFFFFFFFFFFFF: 1,
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF: 1,
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF: 1,  # noqa: E501
                    }
                )
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_sstore_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    expected_post: dict,
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
    # { (SSTORE 0xffffffff 1) (SSTORE 0xffffffffffffffff 1) (SSTORE 0xffffffffffffffffffffffffffffffff 1) (SSTORE 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 1) (SSTORE 32 0xffffffff) (SSTORE 64 0xffffffffffffffff) (SSTORE 128 0xffffffffffffffffffffffffffffffff) (SSTORE 256 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0xFFFFFFFF, value=0x1)
            + Op.SSTORE(key=0xFFFFFFFFFFFFFFFF, value=0x1)
            + Op.SSTORE(key=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, value=0x1)
            + Op.SSTORE(
                key=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                value=0x1,
            )
            + Op.SSTORE(key=0x20, value=0xFFFFFFFF)
            + Op.SSTORE(key=0x40, value=0xFFFFFFFFFFFFFFFF)
            + Op.SSTORE(key=0x80, value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.SSTORE(
                key=0x100,
                value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1f2aee312c3c47bdeb27ff5275fddb33c543e394"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x7FFFFFFFFFFFFFFFFFF)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=tx_gas_limit,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
