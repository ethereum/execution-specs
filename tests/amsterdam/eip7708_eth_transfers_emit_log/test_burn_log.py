"""
EIP-7708 burn log tests.

Tests for [EIP-7708: ETH transfers and burns emit a
log](https://eips.ethereum.org/EIPS/eip-7708).
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
    TransactionLog,
    TransactionReceipt,
    compute_create_address,
)

from .spec import Spec, ref_spec_7708

REFERENCE_SPEC_GIT_PATH = ref_spec_7708.git_path
REFERENCE_SPEC_VERSION = ref_spec_7708.version

pytestmark = pytest.mark.valid_from("Amsterdam")

BASE_FEE = 7
GAS_PRICE = BASE_FEE * 2


def test_burn_log_when_coinbase_selfdestructs(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test EIP-7708 Burn log when coinbase is a same-tx-created contract that
    self-destructs.

    Post-EIP-6780 SELFDESTRUCT only deletes contracts created in the same
    transaction. The test deploys a contract at the pre-computed coinbase
    address whose init code immediately SELFDESTRUCTs to the caller. The
    priority fee credited after execution gives the selfdestructed coinbase a
    positive residual balance, which must produce a Burn log.
    """
    sender = pre.fund_eoa()
    coinbase_addr = compute_create_address(address=sender, nonce=0)

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.SELFDESTRUCT(Op.CALLER),
        gas_limit=200_000,
        gas_price=GAS_PRICE,
        value=0,
        expected_receipt=TransactionReceipt(
            logs=[
                TransactionLog(
                    address=Address(Spec.SYSTEM_ADDRESS),
                    topics=[
                        Spec.BURN_EVENT_TOPIC,
                        Hash(coinbase_addr, left_padding=True),
                    ],
                ),
            ],
        ),
    )

    post = {
        coinbase_addr: Account.NONEXISTENT,
    }

    state_test(
        env=Environment(
            fee_recipient=coinbase_addr,
            base_fee_per_gas=BASE_FEE,
        ),
        pre=pre,
        tx=tx,
        post=post,
    )
