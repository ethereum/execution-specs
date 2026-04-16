"""
Test_suicides_stop_after_suicide.

Ported from:
state_tests/stTransactionTest/SuicidesStopAfterSuicideFiller.json
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
    ["state_tests/stTransactionTest/SuicidesStopAfterSuicideFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicides_stop_after_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_suicides_stop_after_suicide."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_0 = Address(0x0000000000000000000000000000000000000000)
    contract_1 = Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0x7459280)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000,
    )

    # Source: lll
    # {(SELFDESTRUCT 0x0000000000000000000000000000000000000001)}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=0x1) + Op.STOP,
        balance=1110,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # {(SELFDESTRUCT 0) (CALL 30000 0x0000000000000000000000000000000000000000 0 0 0 0 0) }  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=contract_0)
        + Op.CALL(
            gas=0x7530,
            address=contract_0,
            value=contract_0,
            args_offset=contract_0,
            args_size=contract_0,
            ret_offset=contract_0,
            ret_size=contract_0,
        )
        + Op.STOP,
        balance=10000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=Bytes(""),
        gas_limit=83700,
        value=10,
    )

    post = {
        contract_0: Account(storage={}),
        sender: Account(nonce=1),
        contract_1: Account(
            storage={},
            code=bytes.fromhex("6000ff600060006000600060006000617530f100"),
            balance=0,
            nonce=0,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
