"""
Tests for EIP-150 SELFDESTRUCT operation gas costs in the Tangerine
Whistle fork.
"""

from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Op,
    Transaction,
)
from execution_testing.forks import Byzantium
from execution_testing.forks.helpers import Fork

from .spec import ref_spec_150

REFERENCE_SPEC_GIT_PATH = ref_spec_150.git_path
REFERENCE_SPEC_VERSION = ref_spec_150.version


@pytest.mark.pre_alloc_group(
    "selfdestruct_to_precompile_oog",
    reason="Modifies precompile balance, must be isolated in EngineX format",
)
@pytest.mark.parametrize("oog_before_state_access", [True, False])
@pytest.mark.with_all_precompiles
@pytest.mark.valid_from("Tangerine")
def test_selfdestruct_to_precompile_oog(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    precompile: Address,
    oog_before_state_access: bool,
) -> None:
    """
    Test SELFDESTRUCT to precompile with out-of-gas at different boundaries.

    - before_state_access: Precompile not touched (>= Amsterdam).
    - after_state_access: Precompile touched but no balance change
      (>= Amsterdam).
    """
    alice = pre.fund_eoa()

    victim_balance = 100
    victim_code = Op.SELFDESTRUCT(precompile)
    victim = pre.deploy_contract(code=victim_code, balance=victim_balance)

    gas_costs = fork.gas_costs()
    push_cost = gas_costs.G_VERY_LOW
    selfdestruct_cost = gas_costs.G_SELF_DESTRUCT
    # exact gas would be:
    # push_cost + selfdestruct_cost + new_account_cost + G_NEW_ACCOUNT

    if oog_before_state_access:
        gas = push_cost + selfdestruct_cost - 1
    else:
        gas = push_cost + selfdestruct_cost

    caller_code = Op.CALL(gas=gas, address=victim)
    caller = pre.deploy_contract(code=caller_code)

    tx = Transaction(
        sender=alice,
        to=caller,
        gas_limit=100_000,
        protected=True if fork >= Byzantium else False,
    )

    # BAL expectations >= Amsterdam
    expected_block_access_list = None
    if fork.header_bal_hash_required():
        account_expectations: Dict[Address, BalAccountExpectation | None] = {
            alice: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1)
                ],
            ),
            caller: BalAccountExpectation.empty(),
            victim: BalAccountExpectation.empty(),
        }
        if oog_before_state_access:
            # precompile not touched, not in BAL
            account_expectations[precompile] = None
        else:
            # precompile touched, in BAL with empty expectation
            account_expectations[precompile] = BalAccountExpectation.empty()
        expected_block_access_list = BlockAccessListExpectation(
            account_expectations=account_expectations
        )

    # OOG: victim keeps balance and code, precompile unchanged
    post = {
        alice: Account(nonce=1),
        caller: Account(),
        victim: Account(balance=victim_balance, code=victim_code),
        precompile: Account.NONEXISTENT,
    }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=expected_block_access_list,
            )
        ],
        post=post,
    )
