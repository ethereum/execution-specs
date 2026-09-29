"""Tests for the effects of EIP-6110 deposit requests on EIP-7928."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    DepositRequest,
    Header,
    Requests,
    SystemContractInteractionTransaction,
)

from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def test_bal_6110_deposit(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure a deposit reaches the BAL as the deposit contract's balance
    change at the transaction's own index. The request is read from the
    contract's log, so unlike the other request types nothing touches the
    contract at the post-execution index.
    """
    deposit = DepositRequest(
        pubkey=0x01,
        withdrawal_credentials=0x02,
        amount=32_000_000_000,
        signature=0x03,
        index=0x0,
    )
    prepared = SystemContractInteractionTransaction(
        requests=[deposit]
    ).update_pre(pre)
    alice = prepared.sender_account
    deposit_contract = DepositRequest.system_contract_address

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=prepared.transactions(),
                header_verify=Header(requests_hash=Requests(deposit)),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        alice: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
                        ),
                        deposit_contract: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1,
                                    post_balance=deposit.value,
                                )
                            ],
                            nonce_changes=[],
                            code_changes=[],
                        ),
                    }
                ),
            )
        ],
        post={
            alice: Account(nonce=1),
            deposit_contract: Account(balance=deposit.value),
        },
    )
