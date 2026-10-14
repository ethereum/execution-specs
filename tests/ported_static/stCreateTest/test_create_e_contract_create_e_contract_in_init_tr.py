"""
Test_create_e_contract_create_e_contract_in_init_tr.

Ported from:
state_tests/stCreateTest/CREATE_EContractCreateEContractInInit_TrFiller.json
@manually-enhanced: Do not overwrite. Inner-CALL gas and tx `gas_limit`
bumped on Amsterdam to cover EIP-8037 state-gas spill; pre-EIP-8037
unchanged.

"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCreateTest/CREATE_EContractCreateEContractInInit_TrFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_create_e_contract_create_e_contract_in_init_tr(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_create_e_contract_create_e_contract_in_init_tr."""
    # EIP-8037 state-gas spill OoGs the 60k inner CALL.
    inner_call_gas = 60000
    tx_gas_limit = 600000
    if fork.is_eip_enabled(8037):
        inner_call_gas = 200000
        tx_gas_limit = 1_000_000

    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: lll
    # {[[1]]12}
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0xC) + Op.STOP,
        balance=0xE8D4A51000,
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.POP(
            Op.CALL(
                gas=inner_call_gas,
                address=contract_0,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CREATE(value=0x0, offset=0x0, size=0x20),
        gas_limit=tx_gas_limit,
    )

    post = {
        contract_0: Account(storage={1: 12}),
        compute_create_address(address=sender, nonce=0): Account(nonce=2),
    }

    state_test(pre=pre, post=post, tx=tx)
