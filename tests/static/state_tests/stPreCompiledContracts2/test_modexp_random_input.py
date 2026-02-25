"""
Fuzzed input discovered by Guido

Ported from:
tests/static/state_tests/stPreCompiledContracts2/modexpRandomInputFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stPreCompiledContracts2/modexpRandomInputFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit",
    [
        ("00000000000000000000000000000000000000000000000000000000000000e300000000000000000000000000000000000000000000000000", 710000),
        ("00000000000000000000000000000000000000000000000000000000000000e300000000000000000000000000000000000000000000000000", 7000000),
        ("00000000008000000000000000000000000000000000000000000000000000000000000400000000000000000000000a", 710000),
        ("00000000008000000000000000000000000000000000000000000000000000000000000400000000000000000000000a", 7000000),
        ("0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001147000000000000000000000000000000000000000000000000000000000061660350000000000000000000000000000000000000000000000000000000000000008", 710000),
        ("0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001147000000000000000000000000000000000000000000000000000000000061660350000000000000000000000000000000000000000000000000000000000000008", 7000000),
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5'],
)
@pytest.mark.pre_alloc_mutable
def test_modexp_random_input(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
) -> None:
    """Fuzzed input discovered by Guido."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0xd187b36e8532efd7f15218fb1781d79330c0cda2")
    contract = Address("0x0000000000000000000000000000000000000005")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0x3635c9adc5dea00000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x897b12d02d588d8a4fe16ff831cbd4459c6f62f8c845b0ccdd31caf068c84a26"
        ),
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
