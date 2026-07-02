"""
Test_contract_store_clears_success.

Ported from:
state_tests/stTransactionTest/ContractStoreClearsSuccessFiller.json

@manually-enhanced: Do not overwrite. The contract clears 10 cold
storage slots (each 12 -> 0) and the transaction sends value alongside,
so the asserted post is the cleared storage plus the received value.
EIP-8038 raises the cold SSTORE-clear charge from 5000 to 13000, so the
10 clears no longer fit in the original gas limit and the contract runs
out of gas before clearing the storage or keeping the transfer. Bump the
gas limit by the per-clear charge delta times the 10 clears so every
clear still lands at Amsterdam. The delta is derived from the fork gas
model and is exactly 0 pre-EIP-8037; do not hardcode the Amsterdam
value. The post asserts only the target account (cleared storage and the
received value), which holds at every fork once the gas fits.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/ContractStoreClearsSuccessFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_contract_store_clears_success(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_contract_store_clears_success."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0x8583B00)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # {(SSTORE 0 0)(SSTORE 1 0)(SSTORE 2 0)(SSTORE 3 0)(SSTORE 4 0)(SSTORE 5 0)(SSTORE 6 0)(SSTORE 7 0)(SSTORE 8 0)(SSTORE 9 0)}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x0)
        + Op.SSTORE(key=0x1, value=0x0)
        + Op.SSTORE(key=0x2, value=0x0)
        + Op.SSTORE(key=0x3, value=0x0)
        + Op.SSTORE(key=0x4, value=0x0)
        + Op.SSTORE(key=0x5, value=0x0)
        + Op.SSTORE(key=0x6, value=0x0)
        + Op.SSTORE(key=0x7, value=0x0)
        + Op.SSTORE(key=0x8, value=0x0)
        + Op.SSTORE(key=0x9, value=0x0)
        + Op.STOP,
        storage={
            0: 12,
            1: 12,
            2: 12,
            3: 12,
            4: 12,
            5: 12,
            6: 12,
            7: 12,
            8: 12,
            9: 12,
        },
        nonce=0,
    )

    # EIP-8038 raises the cold SSTORE-clear charge; bump the gas limit by
    # the per-clear charge delta times the 10 clears so all of them still
    # land instead of running out of gas before clearing the storage.
    cold_clear_delta = (
        Op.SSTORE.with_metadata(
            key_warm=False, original_value=1, current_value=1, new_value=0
        ).gas_cost(fork)
        - 5000
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=130000 + 10 * cold_clear_delta,
        value=10,
    )

    post = {target: Account(storage={}, balance=10)}

    state_test(env=env, pre=pre, post=post, tx=tx)
