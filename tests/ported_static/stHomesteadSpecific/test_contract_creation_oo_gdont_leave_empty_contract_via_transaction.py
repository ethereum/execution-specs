"""
Test_contract_creation_oo_gdont_leave_empty_contract_via_transaction.

Ported from:
state_tests/stHomesteadSpecific/contractCreationOOGdontLeaveEmptyContractViaTransactionFiller.json
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
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stHomesteadSpecific/contractCreationOOGdontLeaveEmptyContractViaTransactionFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_contract_creation_oo_gdont_leave_empty_contract_via_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_contract_creation_oo_gdont_leave_empty_contract_via_transaction."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_1 = Address(0x1000000000000000000000000000000000000001)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x10C8E0)
    # Source: lll
    # {(SSTORE 1 1)}
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000001),  # noqa: E501
    )
    # Source: lll
    # {(CALL 50000 0x1000000000000000000000000000000000000001 0 0 64 0 64)}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0xC350,
            address=0x1000000000000000000000000000000000000001,
            value=0x0,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.CALL(
            gas=0xC350,
            address=contract_1,
            value=0x0,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        ),
        gas_limit=96000,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(balance=0)
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
