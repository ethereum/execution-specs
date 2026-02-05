"""Tests for the effects of EIP-7702 transactions on EIP-7928."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    BalAccountExpectation,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Fork,
    Initcode,
    Op,
    Transaction,
    Withdrawal,
    compute_create_address,
)
from execution_testing import (
    Macros as Om,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@pytest.mark.parametrize(
    "self_funded",
    [
        pytest.param(False, id="sponsored"),
        pytest.param(True, id="self_funded"),
    ],
)
def test_bal_7702_delegation_create(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    self_funded: bool,
) -> None:
    """Ensure BAL captures creation of EOA delegation."""
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    if not self_funded:
        relayer = pre.fund_eoa()
        sender = relayer
    else:
        sender = alice

    oracle = pre.deploy_contract(code=Op.STOP)

    tx = Transaction(
        sender=sender,
        to=bob,
        value=10,
        gas_limit=1_000_000,
        gas_price=0xA,
        authorization_list=[
            AuthorizationTuple(
                address=oracle,
                nonce=1 if self_funded else 0,
                signer=alice,
            )
        ],
    )

    account_expectations = {
        alice: BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(
                    block_access_index=1, post_nonce=2 if self_funded else 1
                )
            ],
            code_changes=[
                BalCodeChange(
                    block_access_index=1,
                    new_code=Spec7702.delegation_designation(oracle),
                )
            ],
        ),
        bob: BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(block_access_index=1, post_balance=10)
            ]
        ),
        # Oracle must not be present in BAL - the account is never accessed
        oracle: None,
    }

    # For sponsored variant, relayer must also be included in BAL
    if not self_funded:
        account_expectations[relayer] = BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
        )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    post = {
        alice: Account(
            nonce=2 if self_funded else 1,
            code=Spec7702.delegation_designation(oracle),
        ),
        # Bob receives 10 wei
        bob: Account(balance=10),
    }

    # For sponsored variant, include relayer in post state
    if not self_funded:
        post.update({relayer: Account(nonce=1)})

    blockchain_test(
        pre=pre,
        blocks=[block],
        post=post,
    )


@pytest.mark.parametrize(
    "self_funded",
    [
        pytest.param(False, id="sponsored"),
        pytest.param(True, id="self_funded"),
    ],
)
def test_bal_7702_delegation_update(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    self_funded: bool,
) -> None:
    """Ensure BAL captures update of existing EOA delegation."""
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    if not self_funded:
        relayer = pre.fund_eoa()
        sender = relayer
    else:
        sender = alice

    oracle1 = pre.deploy_contract(code=Op.STOP)
    oracle2 = pre.deploy_contract(code=Op.STOP)

    ## Perhaps create a pre-existing delegation,
    ## see `test_bal_7702_delegated_storage_access` since
    ## `test_bal_7702_delegation_create` already tests creation
    tx_create = Transaction(
        sender=sender,
        to=bob,
        value=10,
        gas_limit=1_000_000,
        gas_price=0xA,
        authorization_list=[
            AuthorizationTuple(
                address=oracle1,
                nonce=1 if self_funded else 0,
                signer=alice,
            )
        ],
    )

    tx_update = Transaction(
        nonce=2 if self_funded else 1,
        sender=sender,
        to=bob,
        value=10,
        gas_limit=1_000_000,
        gas_price=0xA,
        authorization_list=[
            AuthorizationTuple(
                address=oracle2,
                nonce=3 if self_funded else 1,
                signer=alice,
            )
        ],
    )

    account_expectations = {
        alice: BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(
                    block_access_index=1, post_nonce=2 if self_funded else 1
                ),
                BalNonceChange(
                    block_access_index=2, post_nonce=4 if self_funded else 2
                ),
            ],
            code_changes=[
                BalCodeChange(
                    block_access_index=1,
                    new_code=Spec7702.delegation_designation(oracle1),
                ),
                BalCodeChange(
                    block_access_index=2,
                    new_code=Spec7702.delegation_designation(oracle2),
                ),
            ],
        ),
        bob: BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(block_access_index=1, post_balance=10),
                BalBalanceChange(block_access_index=2, post_balance=20),
            ]
        ),
        # Both delegation targets must not be present in BAL
        # the account is never accessed
        oracle1: None,
        oracle2: None,
    }

    # For sponsored variant, relayer must also be included in BAL
    if not self_funded:
        account_expectations[relayer] = BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(block_access_index=1, post_nonce=1),
                BalNonceChange(block_access_index=2, post_nonce=2),
            ],
        )

    block = Block(
        txs=[tx_create, tx_update],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    post = {
        # Finally Alice's account should be delegated to oracle2
        alice: Account(
            nonce=4 if self_funded else 2,
            code=Spec7702.delegation_designation(oracle2),
        ),
        # Bob receives 20 wei in total
        bob: Account(balance=20),
    }

    # For sponsored variant, include relayer in post state
    if not self_funded:
        post.update({relayer: Account(nonce=2)})

    blockchain_test(
        pre=pre,
        blocks=[block],
        post=post,
    )


@pytest.mark.parametrize(
    "self_funded",
    [
        pytest.param(False, id="sponsored"),
        pytest.param(True, id="self_funded"),
    ],
)
def test_bal_7702_delegation_clear(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    self_funded: bool,
) -> None:
    """Ensure BAL captures clearing of EOA delegation."""
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    if not self_funded:
        relayer = pre.fund_eoa()
        sender = relayer
    else:
        sender = alice

    oracle = pre.deploy_contract(code=Op.STOP)
    abyss = Spec7702.RESET_DELEGATION_ADDRESS

    ## Perhaps create a pre-existing delegation,
    ## see `test_bal_7702_delegated_storage_access` since
    ## `test_bal_7702_delegation_create` already tests creation
    tx_create = Transaction(
        sender=sender,
        to=bob,
        value=10,
        gas_limit=1_000_000,
        gas_price=0xA,
        authorization_list=[
            AuthorizationTuple(
                address=oracle,
                nonce=1 if self_funded else 0,
                signer=alice,
            )
        ],
    )

    tx_clear = Transaction(
        nonce=2 if self_funded else 1,
        sender=sender,
        to=bob,
        value=10,
        gas_limit=1_000_000,
        gas_price=0xA,
        authorization_list=[
            AuthorizationTuple(
                address=abyss,
                nonce=3 if self_funded else 1,
                signer=alice,
            )
        ],
    )

    account_expectations = {
        alice: BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(
                    block_access_index=1, post_nonce=2 if self_funded else 1
                ),
                BalNonceChange(
                    block_access_index=2, post_nonce=4 if self_funded else 2
                ),
            ],
            code_changes=[
                BalCodeChange(
                    block_access_index=1,
                    new_code=Spec7702.delegation_designation(oracle),
                ),
                BalCodeChange(block_access_index=2, new_code=""),
            ],
        ),
        bob: BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(block_access_index=1, post_balance=10),
                BalBalanceChange(block_access_index=2, post_balance=20),
            ]
        ),
        # Both delegation targets must not be present in BAL
        # the account is never accessed
        oracle: None,
        abyss: None,
    }

    # For sponsored variant, relayer must also be included in BAL
    if not self_funded:
        account_expectations[relayer] = BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(block_access_index=1, post_nonce=1),
                BalNonceChange(block_access_index=2, post_nonce=2),
            ],
        )

    block = Block(
        txs=[tx_create, tx_clear],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    post = {
        # Finally Alice's account should NOT have any code
        alice: Account(nonce=4 if self_funded else 2, code=""),
        # Bob receives 20 wei in total
        bob: Account(balance=20),
    }

    # For sponsored variant, include relayer in post state
    if not self_funded:
        post.update({relayer: Account(nonce=2)})

    blockchain_test(
        pre=pre,
        blocks=[block],
        post=post,
    )


def test_bal_7702_delegated_storage_access(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures storage operations when calling a delegated
    EIP-7702 account.
    """
    # Oracle contract that reads from slot 0x01 and writes to slot 0x02
    oracle = pre.deploy_contract(
        code=Op.SLOAD(0x01) + Op.PUSH1(0x42) + Op.PUSH1(0x02) + Op.SSTORE
    )
    bob = pre.fund_eoa()

    alice = pre.deploy_contract(
        nonce=0x1, code=Spec7702.delegation_designation(oracle), balance=0
    )

    tx = Transaction(
        sender=bob,
        to=alice,  # Bob calls Alice (delegated account)
        value=10,
        gas_limit=1_000_000,
        gas_price=0xA,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(block_access_index=1, post_balance=10)
                    ],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x02,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x42
                                )
                            ],
                        )
                    ],
                    storage_reads=[0x01],
                ),
                bob: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                # Oracle appears in BAL due to account access
                # (delegation target)
                oracle: BalAccountExpectation.empty(),
            }
        ),
    )

    post = {
        alice: Account(
            balance=10,
            storage={0x02: 0x42},
        ),
        bob: Account(nonce=1),
    }

    blockchain_test(
        pre=pre,
        blocks=[block],
        post=post,
    )


def test_bal_7702_invalid_nonce_authorization(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Ensure BAL handles failed authorization due to wrong nonce."""
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)
    relayer = pre.fund_eoa()
    oracle = pre.deploy_contract(code=Op.STOP)

    tx = Transaction(
        sender=relayer,  # Sponsored transaction
        to=bob,
        value=10,
        gas_limit=1_000_000,
        gas_price=0xA,
        authorization_list=[
            AuthorizationTuple(
                address=oracle,
                nonce=5,  # Wrong nonce - Alice's actual nonce is 0
                signer=alice,
            )
        ],
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                # Ensuring silent fail
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(block_access_index=1, post_balance=10)
                    ]
                ),
                relayer: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                # Alice's account was marked warm but no changes were made
                alice: BalAccountExpectation.empty(),
                # Oracle must NOT be present - authorization failed so
                # account is never accessed
                oracle: None,
            }
        ),
    )

    post = {
        relayer: Account(nonce=1),
        bob: Account(balance=10),
    }

    blockchain_test(
        pre=pre,
        blocks=[block],
        post=post,
    )


def test_bal_7702_invalid_chain_id_authorization(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Ensure BAL handles failed authorization due to wrong chain id."""
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)
    relayer = pre.fund_eoa()
    oracle = pre.deploy_contract(code=Op.STOP)

    tx = Transaction(
        sender=relayer,  # Sponsored transaction
        to=bob,
        value=10,
        gas_limit=1_000_000,
        gas_price=0xA,
        authorization_list=[
            AuthorizationTuple(
                chain_id=999,  # Wrong chain id
                address=oracle,
                nonce=0,
                signer=alice,
            )
        ],
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                # Alice's account must not be read because
                # authorization fails before loading her account
                alice: None,
                # Ensuring silent fail
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(block_access_index=1, post_balance=10)
                    ]
                ),
                relayer: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                # Oracle must NOT be present - authorization failed so
                # account never accessed
                oracle: None,
            }
        ),
    )

    post = {
        relayer: Account(nonce=1),
        bob: Account(balance=10),
    }

    blockchain_test(
        # Set chain id here
        # so this test holds if the default is
        # ever changed
        chain_id=1,
        pre=pre,
        blocks=[block],
        post=post,
    )


@pytest.mark.with_all_call_opcodes
def test_bal_7702_delegated_via_call_opcode(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    call_opcode: Op,
) -> None:
    """
    Ensure BAL captures delegation target when a contract uses *CALL
    opcodes to call a delegated account.
    """
    # `oracle` contract that just returns successfully
    oracle = pre.deploy_contract(code=Op.STOP)

    # `alice` is a delegated account pointing to oracle
    alice = pre.deploy_contract(
        nonce=1,
        code=Spec7702.delegation_designation(oracle),
        balance=0,
    )

    # caller contract that uses `call_opcode` to call `alice`
    caller = pre.deploy_contract(code=(call_opcode(address=alice) + Op.STOP))

    bob = pre.fund_eoa()
    tx = Transaction(
        sender=bob,
        to=caller,  # `bob` calls caller contract
        gas_limit=10_000_000,
        gas_price=0xA,
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                bob: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                caller: BalAccountExpectation.empty(),
                # `alice` is accessed due to being the call target
                alice: BalAccountExpectation.empty(),
                # `oracle` appears in BAL due to delegation target access
                oracle: BalAccountExpectation.empty(),
            }
        ),
    )

    post = {bob: Account(nonce=1)}
    blockchain_test(
        pre=pre,
        blocks=[block],
        post=post,
    )


def test_bal_7702_null_address_delegation_no_code_change(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL does not record spurious code changes when delegating to
    NULL_ADDRESS (sets code to empty on an account that already has
    empty code).
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=alice,
        to=bob,
        value=10,
        gas_limit=1_000_000,
        authorization_list=[
            AuthorizationTuple(
                address=0,
                nonce=1,
                signer=alice,
            )
        ],
    )

    # `alice` should appear in BAL with nonce change only, NOT code change
    # because setting code from b"" to b"" is a net-zero change
    account_expectations = {
        alice: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=2)],
            code_changes=[],  # explicit check for no code changes
        ),
        bob: BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(block_access_index=1, post_balance=10)
            ]
        ),
    }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post={
            alice: Account(nonce=2, code=b""),
            bob: Account(balance=10),
        },
    )


@pytest.mark.parametrize(
    "self_funded",
    [
        pytest.param(False, id="sponsored"),
        pytest.param(True, id="self_funded"),
    ],
)
def test_bal_7702_double_auth_reset(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    self_funded: bool,
) -> None:
    """
    Ensure BAL captures the net code change when multiple authorizations
    occur in the same transaction (double auth).

    This test verifies that when:
    1. First auth sets delegation to CONTRACT_A
    2. Second auth resets delegation to empty (address 0)

    Scenario where the transaction is sponsored and self-funded are covered.

    The BAL should show the NET change (empty -> empty), not intermediate
    states. This is a regression test for the bug where the BAL showed
    the first auth's code but the final state was empty.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)
    relayer = pre.fund_eoa()

    contract_a = pre.deploy_contract(code=Op.STOP)

    # Transaction with double auth:
    # 1. First sets delegation to contract_a
    # 2. Second resets to empty
    tx = Transaction(
        sender=alice if self_funded else relayer,
        to=bob,
        value=10,
        gas_limit=1_000_000,
        gas_price=0xA,
        authorization_list=[
            AuthorizationTuple(
                address=contract_a,
                nonce=1 if self_funded else 0,
                signer=alice,
            ),
            AuthorizationTuple(
                address=0,  # Reset to empty
                nonce=2 if self_funded else 1,
                signer=alice,
            ),
        ],
    )

    alice_nonce = 3 if self_funded else 2
    relayer_nonce = 1 if not self_funded else 0
    relayer_bal_expectation = (
        BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)]
        )
        if not self_funded
        else None
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        alice: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1,
                                    post_nonce=alice_nonce,
                                )
                            ],
                            code_changes=[],
                        ),
                        bob: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1, post_balance=10
                                )
                            ]
                        ),
                        relayer: relayer_bal_expectation,
                        contract_a: None,
                    }
                ),
            )
        ],
        post={
            alice: Account(nonce=alice_nonce, code=b""),  # Final code is empty
            bob: Account(balance=10),
            relayer: Account(nonce=relayer_nonce),
        },
    )


def test_bal_7702_double_auth_swap(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures the net code change when double auth swaps
    delegation targets.

    This test verifies that when:
    1. First auth sets delegation to CONTRACT_A
    2. Second auth changes delegation to CONTRACT_B

    The BAL should show the final code change (empty -> CONTRACT_B),
    not the intermediate CONTRACT_A.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)
    relayer = pre.fund_eoa()

    contract_a = pre.deploy_contract(code=Op.STOP)
    contract_b = pre.deploy_contract(code=Op.STOP)

    tx = Transaction(
        sender=relayer,
        to=bob,
        value=10,
        gas_limit=1_000_000,
        gas_price=0xA,
        authorization_list=[
            AuthorizationTuple(
                address=contract_a,
                nonce=0,
                signer=alice,
            ),
            AuthorizationTuple(
                address=contract_b,  # Override to contract_b
                nonce=1,
                signer=alice,
            ),
        ],
    )

    account_expectations = {
        alice: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=2)],
            code_changes=[
                # Should show final code (CONTRACT_B), not CONTRACT_A
                BalCodeChange(
                    block_access_index=1,
                    new_code=Spec7702.delegation_designation(contract_b),
                )
            ],
        ),
        bob: BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(block_access_index=1, post_balance=10)
            ]
        ),
        relayer: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
        ),
        # Neither contract appears in BAL during delegation setup
        contract_a: None,
        contract_b: None,
    }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations
                ),
            )
        ],
        post={
            alice: Account(
                nonce=2, code=Spec7702.delegation_designation(contract_b)
            ),
            bob: Account(balance=10),
            relayer: Account(nonce=1),
        },
    )


def test_bal_selfdestruct_to_7702_delegation(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test BAL with SELFDESTRUCT to 7702 delegated account.

    Tx1: Alice delegates to Oracle.
    Tx2: Victim (balance=100) selfdestructs to Alice.
    SELFDESTRUCT transfers balance without executing recipient code.

    Expected BAL:
    - Alice tx1: code_changes (delegation), nonce_changes
    - Alice tx2: balance_changes (+100)
    - Victim tx2: balance_changes (100→0)
    - Oracle: MUST NOT appear (SELFDESTRUCT doesn't execute recipient code)
    """
    # Alice (EOA) will receive delegation then receive selfdestruct balance
    # Use explicit initial balance for clarity
    alice_initial_balance = 10**18  # 1 ETH default
    alice = pre.fund_eoa(amount=alice_initial_balance)
    bob = pre.fund_eoa(amount=0)  # Just to be the recipient of tx

    # Oracle contract that Alice will delegate to
    oracle = pre.deploy_contract(code=Op.SSTORE(0x01, 0x42) + Op.STOP)

    victim_balance = 100

    # Victim contract that selfdestructs to Alice
    victim = pre.deploy_contract(
        code=Op.SELFDESTRUCT(alice),
        balance=victim_balance,
    )

    # Relayer for tx1 (delegation)
    relayer = pre.fund_eoa()

    # Tx1: Alice authorizes delegation to Oracle
    tx1 = Transaction(
        sender=relayer,
        to=bob,
        value=10,
        gas_limit=1_000_000,
        gas_price=0xA,
        authorization_list=[
            AuthorizationTuple(
                address=oracle,
                nonce=0,
                signer=alice,
            )
        ],
    )

    # Caller contract that triggers selfdestruct on victim
    caller = pre.deploy_contract(code=Op.CALL(100_000, victim, 0, 0, 0, 0, 0))

    # Tx2: Trigger selfdestruct on victim (victim sends balance to Alice)
    tx2 = Transaction(
        nonce=1,
        sender=relayer,
        to=caller,
        gas_limit=1_000_000,
        gas_price=0xA,
    )

    alice_final_balance = alice_initial_balance + victim_balance

    account_expectations = {
        alice: BalAccountExpectation(
            # tx1: nonce change for auth, code change for delegation
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
            code_changes=[
                BalCodeChange(
                    block_access_index=1,
                    new_code=Spec7702.delegation_designation(oracle),
                )
            ],
            # tx2: balance change from selfdestruct
            balance_changes=[
                BalBalanceChange(
                    block_access_index=2, post_balance=alice_final_balance
                )
            ],
        ),
        bob: BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(block_access_index=1, post_balance=10)
            ]
        ),
        relayer: BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(block_access_index=1, post_nonce=1),
                BalNonceChange(block_access_index=2, post_nonce=2),
            ],
        ),
        caller: BalAccountExpectation.empty(),
        # Victim (selfdestructing contract): balance changes to 0
        # Explicitly verify ALL fields to avoid false positives
        victim: BalAccountExpectation(
            nonce_changes=[],  # Contract nonce unchanged
            balance_changes=[
                BalBalanceChange(block_access_index=2, post_balance=0)
            ],
            code_changes=[],  # Code unchanged (post-Cancun SELFDESTRUCT)
            storage_changes=[],  # No storage changes
            storage_reads=[],  # No storage reads
        ),
        # Oracle MUST NOT appear in tx2 - SELFDESTRUCT doesn't execute
        # recipient code, so delegation target is never accessed
        oracle: None,
    }

    block = Block(
        txs=[tx1, tx2],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    post = {
        alice: Account(
            nonce=1,
            code=Spec7702.delegation_designation(oracle),
            balance=alice_final_balance,
        ),
        bob: Account(balance=10),
        relayer: Account(nonce=2),
        # Victim still exists but with 0 balance (post-Cancun SELFDESTRUCT)
        victim: Account(balance=0),
    }

    blockchain_test(
        pre=pre,
        blocks=[block],
        post=post,
    )


GWEI = 10**9


def test_bal_withdrawal_to_7702_delegation(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test BAL with withdrawal to 7702 delegated account.

    Tx1: Alice delegates to Oracle. Withdrawal: 10 gwei to Alice.
    Withdrawals credit balance without executing code.

    Expected BAL:
    - Alice tx1: code_changes (delegation), nonce_changes
    - Alice tx2: balance_changes (+10 gwei)
    - Oracle: MUST NOT appear (withdrawals don't execute recipient code)
    """
    # Alice (EOA) will receive delegation then receive withdrawal
    alice_initial_balance = 10**18  # 1 ETH default
    alice = pre.fund_eoa(amount=alice_initial_balance)
    bob = pre.fund_eoa(amount=0)  # Recipient of tx value

    # Oracle contract that Alice will delegate to
    # If delegation were followed, this would write to storage
    oracle = pre.deploy_contract(code=Op.SSTORE(0x01, 0x42) + Op.STOP)

    # Relayer for the delegation tx
    relayer = pre.fund_eoa()

    withdrawal_amount_gwei = 10

    # Tx1: Alice authorizes delegation to Oracle
    tx1 = Transaction(
        sender=relayer,
        to=bob,
        value=10,
        gas_limit=1_000_000,
        gas_price=0xA,
        authorization_list=[
            AuthorizationTuple(
                address=oracle,
                nonce=0,
                signer=alice,
            )
        ],
    )

    alice_final_balance = alice_initial_balance + (
        withdrawal_amount_gwei * GWEI
    )

    account_expectations = {
        alice: BalAccountExpectation(
            # tx1: nonce change for auth, code change for delegation
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
            code_changes=[
                BalCodeChange(
                    block_access_index=1,
                    new_code=Spec7702.delegation_designation(oracle),
                )
            ],
            # tx2 (withdrawal): balance change
            balance_changes=[
                BalBalanceChange(
                    block_access_index=2, post_balance=alice_final_balance
                )
            ],
        ),
        bob: BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(block_access_index=1, post_balance=10)
            ]
        ),
        relayer: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
        ),
        # Oracle MUST NOT appear - withdrawals don't execute recipient code,
        # so delegation target is never accessed
        oracle: None,
    }

    block = Block(
        txs=[tx1],
        withdrawals=[
            Withdrawal(
                index=0,
                validator_index=0,
                address=alice,
                amount=withdrawal_amount_gwei,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    post = {
        alice: Account(
            nonce=1,
            code=Spec7702.delegation_designation(oracle),
            balance=alice_final_balance,
        ),
        bob: Account(balance=10),
        relayer: Account(nonce=1),
    }

    blockchain_test(
        pre=pre,
        blocks=[block],
        post=post,
    )


@pytest.mark.with_all_create_opcodes
def test_bal_7702_delegated_create(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    create_opcode: Op,
) -> None:
    """
    BAL tracks EIP-7702 delegation indicator write and contract creation.

    Alice sends a type-4 (7702) tx authorizing herself to delegate to
    Deployer code which executes CREATE.
    """
    # Alice (EOA)
    alice_initial_balance = 10**18  # 1 ETH default
    alice = pre.fund_eoa(amount=alice_initial_balance)

    # Simple init code that deploys STOP
    deploy_code = Op.STOP
    init_code = Initcode(deploy_code=deploy_code)

    # Deployer code: CREATE/CREATE2 and store result in slot 0
    deployer_code = Om.MSTORE(init_code) + Op.SSTORE(
        0,
        create_opcode(
            offset=0,
            size=len(init_code),
            init_code_size=len(init_code),
        ),
        original_value=0xDEAD,
    )

    deployer_initial_balance = 10**18  # 1 ETH default
    # Deploy factory
    deployer = pre.deploy_contract(
        code=deployer_code,
        balance=deployer_initial_balance,
        storage={0x00: 0xDEAD},  # Initial value to prove SSTORE works
    )

    # Calculate what the contract address WOULD be
    create_contract_address = compute_create_address(
        address=deployer,
        initcode=init_code,
        nonce=1,
        opcode=create_opcode,
    )

    tx = Transaction(
        sender=alice,
        to=deployer,
        gas_limit=1_000_000,
        authorization_list=[
            AuthorizationTuple(
                address=deployer,
                nonce=1,
                signer=alice,
            )
        ],
    )

    # Calculate gas cost
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    gsc = fork.gas_costs()
    max_refund_quotient = fork.max_refund_quotient()
    gas_used = (
        intrinsic_gas_calculator(
            return_cost_deducted_prior_execution=True,
            authorization_list_or_count=tx.authorization_list,
        )
        + deployer_code.gas_cost(fork)
        + init_code.execution_gas
        + gsc.G_CODE_DEPOSIT_BYTE * len(deploy_code)
    )

    refund_counter = gsc.R_AUTHORIZATION_EXISTING_AUTHORITY

    effective_refund = min(refund_counter, gas_used // max_refund_quotient)
    gas_used_post_refund = gas_used - effective_refund

    assert tx.max_fee_per_gas is not None
    alice_expected_balance = alice_initial_balance - (
        gas_used_post_refund * tx.max_fee_per_gas
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        # sending the tx + delegation processing
                        BalNonceChange(block_access_index=1, post_nonce=2)
                    ],
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=alice_expected_balance,
                        )
                    ],
                    code_changes=[
                        BalCodeChange(
                            block_access_index=1,
                            new_code=Spec7702.delegation_designation(deployer),
                        ),
                    ],
                ),
                deployer: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=2)
                    ],
                    # Storage changes: slot 0 = 0xDEAD → contract_address
                    # since CREATE returned contract_address
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x00,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1,
                                    post_value=create_contract_address,
                                )
                            ],
                        )
                    ],
                ),
                create_contract_address: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    code_changes=[
                        BalCodeChange(block_access_index=1, new_code=Op.STOP)
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(
                nonce=2,
                balance=alice_expected_balance,
                code=Spec7702.delegation_designation(deployer),
            ),
            deployer: Account(
                nonce=2,
                storage={0x00: create_contract_address},
            ),
            create_contract_address: Account(nonce=1, code=Op.STOP),
        },
    )
