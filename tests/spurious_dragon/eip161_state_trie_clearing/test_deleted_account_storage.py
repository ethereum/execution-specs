"""
Deleting an empty account must drop its storage as well, so an account
re-created later in the block starts from empty storage.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Fork,
    Header,
    RecipientType,
    Transaction,
    TransactionReceipt,
)

from .spec import ref_spec_161

REFERENCE_SPEC_GIT_PATH = ref_spec_161.git_path
REFERENCE_SPEC_VERSION = ref_spec_161.version

# TODO: Deletion of an empty account that holds storage stays undefined
# for clients until EIP-8253 (Hegota) bumps the nonce of the mainnet
# accounts of that shape. Revisit this test once EIP-8253 ships: unskip
# it or drop it. See PR #3508.
STORAGE_ONLY_ACCOUNT_SKIP = pytest.mark.skip(
    reason="Undefined until EIP-8253 (Hegota), see PR #3508"
)


@STORAGE_ONLY_ACCOUNT_SKIP
@pytest.mark.valid_from("London")
@pytest.mark.pre_alloc_mutable
def test_zero_tip_deletes_coinbase_storage(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a zero-tip fee credit deletes an empty coinbase together
    with its pre-existing storage, so a later transaction in the block
    re-creates the account with empty storage.
    """
    coinbase = pre.fund_eoa(amount=0)
    pre[coinbase] = Account(storage={0x01: 0x01})

    genesis_environment = Environment(base_fee_per_gas=7)
    base_fee_per_gas = fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=7,
        parent_gas_used=0,
        parent_gas_limit=genesis_environment.gas_limit,
    )

    sender = pre.fund_eoa()
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    touch_gas = intrinsic_cost()
    touch_tx = Transaction(
        sender=sender,
        to=pre.fund_eoa(amount=1),
        gas_price=base_fee_per_gas,
        expected_receipt=TransactionReceipt(cumulative_gas_used=touch_gas),
    )
    # The deleted coinbase is a new account again for the second transfer.
    fund_gas = intrinsic_cost(
        sends_value=True
    ) + fork.transaction_top_frame_gas_calculator()(
        sends_value=True, recipient_type=RecipientType.EMPTY_ACCOUNT
    )
    fund_tx = Transaction(
        sender=sender,
        to=coinbase,
        value=1,
        gas_price=base_fee_per_gas,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=touch_gas + fund_gas
        ),
    )

    blockchain_test(
        pre=pre,
        genesis_environment=genesis_environment,
        # Before the merge the coinbase also collects the block reward.
        post={
            coinbase: Account(
                nonce=0,
                balance=1 + fork.get_reward(),
                code=b"",
                storage={},
            ),
        },
        blocks=[
            Block(
                txs=[touch_tx, fund_tx],
                fee_recipient=coinbase,
                header_verify=Header(base_fee_per_gas=base_fee_per_gas),
            )
        ],
    )
