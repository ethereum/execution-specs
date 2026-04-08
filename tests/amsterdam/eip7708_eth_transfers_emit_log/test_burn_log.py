"""
EIP-7708 burn log tests.

Tests for [EIP-7708: ETH transfers and burns emit a
log](https://eips.ethereum.org/EIPS/eip-7708).

Test that Burn logs are emitted for selfdestructed accounts that hold a
positive balance at finalization time.
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
GAS_PRICE = BASE_FEE * 2  # Priority fee = BASE_FEE per unit of gas


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

    This is a regression test for
    https://github.com/erigontech/erigon/issues/19951.
    """
    sender = pre.fund_eoa()

    # The CREATE address is deterministic: keccak(rlp([sender, nonce])).
    # Set the block's fee_recipient (coinbase) to this address so that the
    # priority fee flows to the contract that will self-destruct.
    coinbase_addr = compute_create_address(address=sender, nonce=0)

    # Init code: CALLER SELFDESTRUCT (0x33 0xFF).
    # The constructor pushes the tx sender onto the stack and then
    # self-destructs, sending any contract balance to the sender.
    # Post-EIP-6780 this deletes the contract because it was created
    # in the same transaction.
    initcode = Op.SELFDESTRUCT(Op.CALLER)

    tx = Transaction(
        sender=sender,
        to=None,  # contract creation
        data=initcode,
        gas_limit=200_000,
        gas_price=GAS_PRICE,
        value=0,
        expected_receipt=TransactionReceipt(
            logs=[
                # The only EIP-7708 log: Burn for the selfdestructed coinbase
                # whose residual balance is the priority fee.
                TransactionLog(
                    address=Address(Spec.SYSTEM_ADDRESS),
                    topics=[
                        Spec.BURN_EVENT_TOPIC,
                        Hash(coinbase_addr, left_padding=True),
                    ],
                    # data = burned amount; left unspecified because the exact
                    # gas usage (and therefore tip) depends on the fork's
                    # intrinsic-gas formula, which may change. The framework
                    # skips verification of None fields.
                ),
            ],
        ),
    )

    post = {
        # The selfdestructed coinbase is deleted after finalization
        # (balance cleared, EIP-161 removes the empty account).
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
