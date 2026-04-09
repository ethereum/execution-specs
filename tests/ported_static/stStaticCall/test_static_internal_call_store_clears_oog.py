"""
Test_static_internal_call_store_clears_oog.

Ported from:
state_tests/stStaticCall/static_InternalCallStoreClearsOOGFiller.json
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_InternalCallStoreClearsOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_internal_call_store_clears_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_internal_call_store_clears_oog."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_0 = Address(0x0000000000000000000000000000000000000000)
    contract_1 = Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0x5F5E100)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # {(SSTORE 0 0)(SSTORE 1 0)(SSTORE 2 0)(SSTORE 3 0)(SSTORE 4 0)(SSTORE 5 0)(SSTORE 6 0)(SSTORE 7 0)(SSTORE 8 0)(SSTORE 9 0)}  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=contract_0, value=contract_0)
        + Op.SSTORE(key=0x1, value=contract_0)
        + Op.SSTORE(key=0x2, value=contract_0)
        + Op.SSTORE(key=0x3, value=contract_0)
        + Op.SSTORE(key=0x4, value=contract_0)
        + Op.SSTORE(key=0x5, value=contract_0)
        + Op.SSTORE(key=0x6, value=contract_0)
        + Op.SSTORE(key=0x7, value=contract_0)
        + Op.SSTORE(key=0x8, value=contract_0)
        + Op.SSTORE(key=0x9, value=contract_0)
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
    # Source: lll
    # { [[ 1 ]] (STATICCALL 40000 0 0 0 0 0) }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x9C40,
                address=contract_0,
                args_offset=contract_0,
                args_size=contract_0,
                ret_offset=contract_0,
                ret_size=contract_0,
            ),
        )
        + Op.STOP,
        balance=10,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=Bytes(""),
        gas_limit=160000,
        value=10,
    )

    post = {
        contract_0: Account(
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
            balance=0,
        ),
        sender: Account(nonce=1),
        contract_1: Account(storage={1: contract_0}, balance=20),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
