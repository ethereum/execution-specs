"""
Test_suicides_and_internal_call_suicides_bonus_gas_at_call_failed.

Ported from:
state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesBonusGasAtCallFailedFiller.json
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
    [
        "state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesBonusGasAtCallFailedFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicides_and_internal_call_suicides_bonus_gas_at_call_failed(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_suicides_and_internal_call_suicides_bonus_gas_at_call_failed."""
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
    # {(SELFDESTRUCT 0x0000000000000000000000000000000000000001)}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=0x1) + Op.STOP,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # {(CALL 0 0x0000000000000000000000000000000000000000 0 0 0 0 0) (SELFDESTRUCT 0)}  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=contract_0,
                address=contract_0,
                value=contract_0,
                args_offset=contract_0,
                args_size=contract_0,
                ret_offset=contract_0,
                ret_size=contract_0,
            )
        )
        + Op.SELFDESTRUCT(address=contract_0)
        + Op.STOP,
        balance=10,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=Bytes(""),
        gas_limit=50000,
        value=10,
    )

    post = {contract_0: Account(code=bytes.fromhex("6001ff00"), balance=20)}

    state_test(env=env, pre=pre, post=post, tx=tx)
