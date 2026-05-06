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

    Total::

        N = 2C + A
          = 2(3) + 2
          = 8

    Per-property breakdown::

        wrong (Correctness)         = C   = 3
        missing per change (Compl.) = C   = 3
        missing per account (Compl.)= A   = 2
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
        # wrong (3)
        f"{alice}__wrong__nonce__1",
        f"{alice}__wrong__balance__1",
        f"{bob}__wrong__balance__1",
        # missing per change (3)
        f"{alice}__missing__nonce__1",
        f"{alice}__missing__balance__1",
        f"{bob}__missing__balance__1",
        # missing per account (2)
        f"{alice}__missing",
        f"{bob}__missing",
    }

    assert len(cases) == 8
    assert {c.id for c in cases} == expected_ids
