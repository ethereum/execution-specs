"""Test execution gas after the EIP-7981 access list surcharge."""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Alloc,
    EIPChecklist,
    Fork,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .spec import ref_spec_7981

REFERENCE_SPEC_GIT_PATH = ref_spec_7981.git_path
REFERENCE_SPEC_VERSION = ref_spec_7981.version

pytestmark = pytest.mark.valid_at("EIP7981")


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type in (1, 2))
@pytest.mark.parametrize("gas_delta", [-1, 0, 1])
def test_execution_gas_after_access_list_surcharge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    gas_delta: int,
) -> None:
    """Pin the execution OOG boundary after deducting the surcharge."""
    code = Op.SSTORE(
        0, 2, key_warm=True, original_value=1, current_value=1, new_value=2
    )
    contract = pre.deploy_contract(code=code, storage={0: 1})
    access_list = [AccessList(address=contract, storage_keys=[Hash(0)])]
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list, return_cost_deducted_prior_execution=True
    )
    required_gas = intrinsic + code.gas_cost(fork)
    succeeds = gas_delta >= 0
    tx = Transaction(
        ty=tx_type,
        sender=pre.fund_eoa(),
        to=contract,
        access_list=access_list,
        gas_limit=required_gas + gas_delta,
        expected_receipt=TransactionReceipt(
            status=int(succeeds),
            gas_used=required_gas if succeeds else required_gas - 1,
        ),
    )
    state_test(
        pre=pre,
        post={contract: Account(storage={0: 2 if succeeds else 1})},
        tx=tx,
    )
