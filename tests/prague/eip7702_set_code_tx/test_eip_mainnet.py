"""
abstract: Crafted tests for mainnet of [EIP-7702: Set EOA account code for one transaction](https://eips.ethereum.org/EIPS/eip-7702).
"""  # noqa: E501

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Alloc,
    AuthorizationTuple,
    StateTestFiller,
    Storage,
    Transaction,
)
from ethereum_test_tools import Opcodes as Op

from .spec import Spec, ref_spec_7702

REFERENCE_SPEC_GIT_PATH = ref_spec_7702.git_path
REFERENCE_SPEC_VERSION = ref_spec_7702.version

pytestmark = [pytest.mark.valid_at("Prague"), pytest.mark.mainnet]


def test_eip_7702(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test the executing a simple SSTORE in a set-code transaction."""
    storage = Storage()
    sender = pre.fund_eoa()
    auth_signer = sender

    tx_value = 1

    set_code = (
        Op.SSTORE(storage.store_next(sender), Op.ORIGIN)
        + Op.SSTORE(storage.store_next(sender), Op.CALLER)
        + Op.SSTORE(storage.store_next(tx_value), Op.CALLVALUE)
        + Op.STOP
    )
    set_code_to_address = pre.deploy_contract(
        set_code,
    )
    authorization_list = [
        AuthorizationTuple(
            address=set_code_to_address,
            nonce=1,
            signer=auth_signer,
        ),
    ]
    gas_costs = fork.gas_costs()
    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas_cost = intrinsic_gas_cost_calc(
        access_list=[],
        authorization_list_or_count=authorization_list,
    )
    execution_cost = (
        (gas_costs.G_COLD_SLOAD + gas_costs.G_STORAGE_SET) * 3
        + (gas_costs.G_VERY_LOW * 3)
        + (gas_costs.G_BASE * 3)
    )

    tx = Transaction(
        gas_limit=intrinsic_gas_cost + execution_cost,
        to=auth_signer,
        value=tx_value,
        authorization_list=authorization_list,
        sender=sender,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            set_code_to_address: Account(
                storage=dict.fromkeys(storage, 0),
            ),
            auth_signer: Account(
                nonce=2,
                code=Spec.delegation_designation(set_code_to_address),
                storage=storage,
            ),
        },
    )
