"""Tests for the effects of EIP-7702 transactions on EIP-7928."""

import pytest

from ethereum_test_tools import (
    Account,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Transaction,
)
from ethereum_test_types.block_access_list import (
    BalAccountExpectation,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessListExpectation,
)
from ethereum_test_vm import Opcodes as Op

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
            nonce_changes=[BalNonceChange(tx_index=1, post_nonce=2 if self_funded else 1)],
            code_changes=[
                BalCodeChange(tx_index=1, new_code=Spec7702.delegation_designation(oracle))
            ],
        ),
        bob: BalAccountExpectation(
            balance_changes=[BalBalanceChange(tx_index=1, post_balance=10)]
        ),
        # Oracle must not be present in BAL - the account is never accessed
        oracle: None,
    }

    # For sponsored variant, relayer must also be included in BAL
    if not self_funded:
        account_expectations[relayer] = BalAccountExpectation(
            nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
        )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    post = {
        alice: Account(
            nonce=2 if self_funded else 1, code=Spec7702.delegation_designation(oracle)
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

    ## Perhaps create pre existing delegation,
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
                BalNonceChange(tx_index=1, post_nonce=2 if self_funded else 1),
                BalNonceChange(tx_index=2, post_nonce=4 if self_funded else 2),
            ],
            code_changes=[
                BalCodeChange(tx_index=1, new_code=Spec7702.delegation_designation(oracle1)),
                BalCodeChange(tx_index=2, new_code=Spec7702.delegation_designation(oracle2)),
            ],
        ),
        bob: BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(tx_index=1, post_balance=10),
                BalBalanceChange(tx_index=2, post_balance=20),
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
                BalNonceChange(tx_index=1, post_nonce=1),
                BalNonceChange(tx_index=2, post_nonce=2),
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
            nonce=4 if self_funded else 2, code=Spec7702.delegation_designation(oracle2)
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

    ## Perhaps create  pre existing delegation,
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
                BalNonceChange(tx_index=1, post_nonce=2 if self_funded else 1),
                BalNonceChange(tx_index=2, post_nonce=4 if self_funded else 2),
            ],
            code_changes=[
                BalCodeChange(tx_index=1, new_code=Spec7702.delegation_designation(oracle)),
                BalCodeChange(tx_index=2, new_code=""),
            ],
        ),
        bob: BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(tx_index=1, post_balance=10),
                BalBalanceChange(tx_index=2, post_balance=20),
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
                BalNonceChange(tx_index=1, post_nonce=1),
                BalNonceChange(tx_index=2, post_nonce=2),
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
    oracle = pre.deploy_contract(code=Op.SLOAD(0x01) + Op.PUSH1(0x42) + Op.PUSH1(0x02) + Op.SSTORE)
    bob = pre.fund_eoa()

    alice = pre.deploy_contract(nonce=0x1, code=Spec7702.delegation_designation(oracle), balance=0)

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
                    balance_changes=[BalBalanceChange(tx_index=1, post_balance=10)],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x02,
                            slot_changes=[BalStorageChange(tx_index=1, post_value=0x42)],
                        )
                    ],
                    storage_reads=[0x01],
                ),
                bob: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
                    balance_changes=[BalBalanceChange(tx_index=1, post_balance=10)]
                ),
                relayer: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
                    balance_changes=[BalBalanceChange(tx_index=1, post_balance=10)]
                ),
                relayer: BalAccountExpectation(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
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
