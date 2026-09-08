"""Unit tests for the BAL corruption catalog."""

from execution_testing.base_types import Address
from execution_testing.test_types.block_access_list import (
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    BlockAccessListExpectation,
)
from execution_testing.test_types.block_access_list.account_changes import (
    BalCodeChange,
    BalStorageChange,
    BalStorageSlot,
)
from execution_testing.test_types.block_access_list.corruptions import (
    enumerate_corruptions,
)

ETH = 10**18

ALICE = Address(0xA11CE)
BOB = Address(0xB0B)
ORACLE = Address(0x04AC1E)


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


def test_enumerate_corruptions_complex() -> None:
    """
    Two-transaction block exercising every change kind. Gas ignored.

    Tx 1: Alice deploys contract Oracle and sends 1 ETH on creation.
          alice: nonce@1, balance@1 (5→4 ETH);
          oracle: nonce@1 (EIP-161 contract-creation bump),
                  balance@1 (0→1 ETH), code@1.
    Tx 2: Alice calls Oracle and sends 1 ETH. Oracle reads slot 0x42 and
          writes slot 0x43@2.
          alice: nonce@2, balance@2 (4→3 ETH);
          oracle: balance@2 (1→2 ETH), storage@0x43, storage_read@0x42.

    Shape counts::

        A = 2     (alice, oracle)
        C = 10    (alice.nonce x2, alice.balance x2,
                   oracle.nonce, oracle.balance x2, oracle.code,
                   oracle.storage_write, oracle.storage_read)

    Total::

        N = 2C + A
          = 2(10) + 2
          = 22
    """
    expectation = BlockAccessListExpectation(
        account_expectations={
            ALICE: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1),
                    BalNonceChange(block_access_index=2, post_nonce=2),
                ],
                balance_changes=[
                    BalBalanceChange(
                        block_access_index=1, post_balance=4 * ETH
                    ),
                    BalBalanceChange(
                        block_access_index=2, post_balance=3 * ETH
                    ),
                ],
            ),
            ORACLE: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1),
                ],
                balance_changes=[
                    BalBalanceChange(
                        block_access_index=1, post_balance=1 * ETH
                    ),
                    BalBalanceChange(
                        block_access_index=2, post_balance=2 * ETH
                    ),
                ],
                code_changes=[
                    BalCodeChange(block_access_index=1, new_code=b"\x60\x60"),
                ],
                storage_changes=[
                    BalStorageSlot(
                        slot=0x43,
                        slot_changes=[
                            BalStorageChange(
                                block_access_index=2, post_value=99
                            ),
                        ],
                    ),
                ],
                storage_reads=[0x42],
            ),
        }
    )

    cases = enumerate_corruptions(expectation)

    alice = str(ALICE)
    oracle = str(ORACLE)

    expected_ids = {
        # wrong (10)
        f"{alice}__wrong__nonce__1",
        f"{alice}__wrong__nonce__2",
        f"{alice}__wrong__balance__1",
        f"{alice}__wrong__balance__2",
        f"{oracle}__wrong__nonce__1",
        f"{oracle}__wrong__balance__1",
        f"{oracle}__wrong__balance__2",
        f"{oracle}__wrong__code__1",
        f"{oracle}__wrong__storage__0x43__2",
        f"{oracle}__wrong__storage_read__0x42",
        # missing per change (10)
        f"{alice}__missing__nonce__1",
        f"{alice}__missing__nonce__2",
        f"{alice}__missing__balance__1",
        f"{alice}__missing__balance__2",
        f"{oracle}__missing__nonce__1",
        f"{oracle}__missing__balance__1",
        f"{oracle}__missing__balance__2",
        f"{oracle}__missing__code__1",
        f"{oracle}__missing__storage__0x43__2",
        f"{oracle}__missing__storage_read__0x42",
        # missing per account (2)
        f"{alice}__missing",
        f"{oracle}__missing",
    }

    assert len(cases) == 22
    assert {c.id for c in cases} == expected_ids
