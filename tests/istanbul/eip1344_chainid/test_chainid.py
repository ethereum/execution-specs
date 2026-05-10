"""
Tests [EIP-1344: CHAINID opcode](https://eips.ethereum.org/EIPS/eip-1344).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    ChainConfig,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-1344.md"
REFERENCE_SPEC_VERSION = "02e46aebc80e6e5006ab4d2daa41876139f9a9e2"


@pytest.mark.with_all_typed_transactions(
    marks=lambda tx_type: (
        pytest.mark.execute(
            pytest.mark.skip(
                reason="type 3 transactions aren't supported in execute mode"
            )
        )
        if tx_type == 3
        else None
    )
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stChainId/chainIdFiller.json",
    ],
)
@pytest.mark.valid_from("Istanbul")
def test_chainid(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    chain_config: ChainConfig,
    typed_transaction: Transaction,
) -> None:
    """Test CHAINID opcode."""
    chain_id = chain_config.chain_id
    contract_code = Op.SSTORE(1, Op.CHAINID) + Op.STOP
    contract_address = pre.deploy_contract(contract_code)

    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    # Tx-type-specific intrinsic args derived from the parametrized fixture.
    intrinsic_kwargs: dict = {"calldata": typed_transaction.data}
    if typed_transaction.access_list:
        intrinsic_kwargs["access_list"] = typed_transaction.access_list
    if typed_transaction.authorization_list:
        intrinsic_kwargs["authorization_list_or_count"] = (
            typed_transaction.authorization_list
        )

    tx = typed_transaction.copy(
        chain_id=chain_id,
        to=contract_address,
        gas_limit=(
            intrinsic_calc(**intrinsic_kwargs)
            + contract_code.gas_cost(fork)
            + fork.sstore_state_gas()
        ),
    )

    post = {
        contract_address: Account(storage={1: chain_id}),
    }

    state_test(pre=pre, post=post, tx=tx)
