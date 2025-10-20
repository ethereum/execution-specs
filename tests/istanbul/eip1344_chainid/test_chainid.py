"""
Tests [EIP-1344: CHAINID opcode](https://eips.ethereum.org/EIPS/eip-1344).
"""

import pytest

from ethereum_test_tools import Account, Alloc, ChainConfig, StateTestFiller, Transaction
from ethereum_test_vm import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-1344.md"
REFERENCE_SPEC_VERSION = "02e46aebc80e6e5006ab4d2daa41876139f9a9e2"


@pytest.mark.with_all_typed_transactions(
    marks=lambda tx_type: pytest.mark.execute(
        pytest.mark.skip(reason="type 3 transactions aren't supported in execute mode")
    )
    if tx_type == 3
    else None
)
@pytest.mark.valid_from("Istanbul")
def test_chainid(
    state_test: StateTestFiller,
    pre: Alloc,
    chain_config: ChainConfig,
    typed_transaction: Transaction,
) -> None:
    """Test CHAINID opcode."""
    chain_id = chain_config.chain_id
    contract_address = pre.deploy_contract(Op.SSTORE(1, Op.CHAINID) + Op.STOP)

    tx = typed_transaction.copy(
        chain_id=chain_id,
        to=contract_address,
    )

    post = {
        contract_address: Account(storage={1: chain_id}),
    }

    state_test(pre=pre, post=post, tx=tx)
