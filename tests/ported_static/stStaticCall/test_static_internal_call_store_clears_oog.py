"""
Test_static_internal_call_store_clears_oog.

Ported from:
state_tests/stStaticCall/static_InternalCallStoreClearsOOGFiller.json
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
    ["state_tests/stStaticCall/static_InternalCallStoreClearsOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_internal_call_store_clears_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_internal_call_store_clears_oog."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_0 = Address("0x0000000000000000000000000000000000000000")
    contract_1 = Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # {(SSTORE 0 0)(SSTORE 1 0)(SSTORE 2 0)(SSTORE 3 0)(SSTORE 4 0)(SSTORE 5 0)(SSTORE 6 0)(SSTORE 7 0)(SSTORE 8 0)(SSTORE 9 0)}  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
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
        address=Address("0x0000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5F5E100)
    # Source: lll
    # { [[ 1 ]] (STATICCALL 40000 0 0 0 0 0) }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x9C40,
                address=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=10,
        nonce=0,
        address=Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_1,
        gas_limit=160000,
        value=10,
        gas_price=10,
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
        contract_1: Account(storage={1: 0}, balance=20),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
