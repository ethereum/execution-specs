"""Unit tests for the BAL corruption catalog."""

from execution_testing.base_types import Address
from execution_testing.test_types.block_access_list import (
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    BlockAccessListExpectation,
)
from execution_testing.test_types.block_access_list.corruptions import (
    enumerate_corruptions,
)

ETH = 10**18

ALICE = Address(0xA11CE)
BOB = Address(0xB0B)


def test_enumerate_corruptions_alice_bob() -> None:
    """
    Alice starts with 5 ETH and transfers 1 ETH to Bob. Gas is ignored
    for simplicity — so Alice ends with 4 ETH and Bob with 1 ETH.

    Shape counts::

        A = 2    (alice, bob)
        C = 3    (alice.nonce, alice.balance, bob.balance)
        R = 0
        K = 3    (alice.nonce_changes, alice.balance_changes,
                  bob.balance_changes)
        α = 1    (A ≥ 2)
        β = 0    (only block_access_index=1 appears)

    Total::

        N = 2C + R + K + 6A + 1 + α + β
          = 2(3) + 0 + 3 + 6(2) + 1 + 1 + 0
          = 23

    Per-prefix breakdown::

        corrupt_    = C           = 3
        omit_       = K + A       = 5
        duplicate_  = C + R       = 3
        phantom_    = 1 + 5A      = 11
        swap_       = α + β       = 1
    """
    expectation = BlockAccessListExpectation(
        account_expectations={
            ALICE: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1),
                ],
                balance_changes=[
                    BalBalanceChange(
                        block_access_index=1, post_balance=4 * ETH
                    ),
                ],
            ),
            BOB: BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(
                        block_access_index=1, post_balance=1 * ETH
                    ),
                ],
            ),
        }
    )

    cases = enumerate_corruptions(expectation)

    alice = str(ALICE)
    bob = str(BOB)

    expected_ids = {
        # corrupt_ (3)
        f"{alice}__corrupt_nonce",
        f"{alice}__corrupt_balance",
        f"{bob}__corrupt_balance",
        # omit_ (5)
        f"{alice}__omit_nonce",
        f"{alice}__omit_balance",
        f"{bob}__omit_balance",
        f"{alice}__omit_account",
        f"{bob}__omit_account",
        # duplicate_ (3)
        f"{alice}__duplicate_nonce",
        f"{alice}__duplicate_balance",
        f"{bob}__duplicate_balance",
        # phantom_ (11)
        "phantom_account",
        f"{alice}__phantom_nonce",
        f"{alice}__phantom_balance",
        f"{alice}__phantom_code",
        f"{alice}__phantom_storage_write",
        f"{alice}__phantom_storage_read",
        f"{bob}__phantom_nonce",
        f"{bob}__phantom_balance",
        f"{bob}__phantom_code",
        f"{bob}__phantom_storage_write",
        f"{bob}__phantom_storage_read",
        # swap_ (1)
        "swap_accounts",
    }

    assert len(cases) == 23
    assert {c.id for c in cases} == expected_ids
