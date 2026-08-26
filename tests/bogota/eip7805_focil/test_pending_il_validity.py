"""Tests EIP-7805 FOCIL appendability of omitted IL txs by tx validity."""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Fork,
    Hash,
    Op,
    Transaction,
    add_kzg_version,
)
from execution_testing.base_types import HexNumber
from execution_testing.test_types.transaction_types import (
    TransactionDefaults,
)

from ethereum.crypto.elliptic_curve import SECP256K1N
from ethereum.forks.amsterdam.transactions import VERSIONED_HASH_VERSION_KZG

from .spec import ref_spec_7805

REFERENCE_SPEC_GIT_PATH = ref_spec_7805.git_path
REFERENCE_SPEC_VERSION = ref_spec_7805.version

pytestmark = [
    pytest.mark.valid_from("Bogota"),
    pytest.mark.blockchain_test_engine_only,
]


@pytest.mark.parametrize(
    "scenario",
    [
        "appendable",
        "invalid_nonce",
        pytest.param("old_nonce", marks=pytest.mark.pre_alloc_mutable),
        "replayed_nonce",
        pytest.param("max_nonce", marks=pytest.mark.pre_alloc_mutable),
        pytest.param(
            "max_nonce_minus_one", marks=pytest.mark.pre_alloc_mutable
        ),
        "mix_invalid_and_appendable",
    ],
)
def test_pending_il_appendability_by_nonce(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    scenario: str,
) -> None:
    """
    A pending IL tx is appendable only with a currently-valid nonce.

    With ample block gas the pending tx always fits, so appendability depends
    only on whether its nonce matches its sender's post-execution nonce. A
    single appendable pending tx is enough to leave the block unsatisfied.
    """
    recipient = pre.nonexistent_account()

    def pending_tx(
        *, nonce: int = 0, account_nonce: int | None = None
    ) -> Transaction:
        return Transaction(
            sender=pre.fund_eoa(nonce=account_nonce),
            to=recipient,
            nonce=nonce,
            value=1,
        )

    block_txs: list[Transaction] = []
    match scenario:
        case "appendable":
            pending = [pending_tx()]
            expected_satisfied = False
        case "invalid_nonce":
            pending = [pending_tx(nonce=1)]
            expected_satisfied = True
        case "old_nonce":
            pending = [pending_tx(nonce=0, account_nonce=1)]
            expected_satisfied = True
        case "replayed_nonce":
            replayed_sender = pre.fund_eoa()
            block_txs = [
                Transaction(
                    sender=replayed_sender, to=recipient, nonce=0, value=2
                )
            ]
            pending = [
                Transaction(
                    sender=replayed_sender, to=recipient, nonce=0, value=1
                )
            ]
            expected_satisfied = True
        case "max_nonce":
            pending = [pending_tx(nonce=2**64 - 1, account_nonce=2**64 - 1)]
            expected_satisfied = True
        case "max_nonce_minus_one":
            pending = [pending_tx(nonce=2**64 - 2, account_nonce=2**64 - 2)]
            expected_satisfied = False
        case "mix_invalid_and_appendable":
            pending = [pending_tx(), pending_tx(nonce=1)]
            expected_satisfied = False
        case _:
            raise ValueError(f"unknown scenario: {scenario}")

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=block_txs,
                inclusion_list_txs=pending,
                expected_inclusion_list_satisfied=expected_satisfied,
            )
        ],
    )


@pytest.mark.parametrize(
    "scenario",
    [
        "affordable",
        "cannot_afford",
        "exactly_affordable",
        "one_wei_short",
        "unaffordable_due_to_calldata",
    ],
)
def test_pending_il_appendability_by_affordability(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    scenario: str,
) -> None:
    """
    A pending IL tx is appendable only if its sender can afford it.

    With ample block gas the pending tx always fits, so appendability depends
    only on whether the sender's balance covers ``gas_limit * gas_price``.
    The explicit gas limit fixes that cost; the calldata case shows a single
    non-zero byte lifting the cost just past an otherwise-sufficient balance.
    """
    calc = fork.transaction_intrinsic_cost_calculator()
    simple_transfer_gas = calc()
    one_nonzero_byte_gas = calc(calldata=b"\x01")
    gas_price = TransactionDefaults.gas_price
    transfer_cost = simple_transfer_gas * gas_price
    recipient = pre.nonexistent_account()

    def pending_tx(
        *,
        gas_limit: int = simple_transfer_gas,
        balance: int = 10**18,
        data: bytes = b"",
    ) -> Transaction:
        sender = pre.fund_eoa(amount=balance)
        return Transaction(
            sender=sender,
            to=recipient,
            gas_limit=gas_limit,
            data=data,
        )

    match scenario:
        case "affordable":
            pending = [pending_tx()]
            expected_satisfied = False
        case "cannot_afford":
            pending = [pending_tx(balance=0)]
            expected_satisfied = True
        case "exactly_affordable":
            pending = [pending_tx(balance=transfer_cost)]
            expected_satisfied = False
        case "one_wei_short":
            pending = [pending_tx(balance=transfer_cost - 1)]
            expected_satisfied = True
        case "unaffordable_due_to_calldata":
            pending = [
                pending_tx(
                    gas_limit=one_nonzero_byte_gas,
                    balance=transfer_cost,
                    data=b"\x01",
                )
            ]
            expected_satisfied = True
        case _:
            raise ValueError(f"unknown scenario: {scenario}")

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=pending,
                expected_inclusion_list_satisfied=expected_satisfied,
            )
        ],
    )


@pytest.mark.parametrize(
    "signature_type",
    [
        "valid",
        "all_zeros",
        "invalid_s",
    ],
)
def test_block_with_invalid_signature_pending_il_tx_is_valid(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    signature_type: str,
) -> None:
    """
    A pending IL tx with an invalid signature may be omitted.

    FOCIL reuses normal transaction validation for missing IL transactions.
    If the signature is invalid, the tx is not appendable and omission is
    allowed.
    """
    sender = pre.fund_eoa()
    recipient = pre.nonexistent_account()
    calc = fork.transaction_intrinsic_cost_calculator()
    simple_transfer_gas = calc()
    signed_tx = Transaction(
        sender=sender,
        to=recipient,
        gas_limit=simple_transfer_gas,
    ).with_signature_and_sender()
    expected_satisfied = True
    match signature_type:
        case "valid":
            expected_satisfied = False
        case "all_zeros":
            signed_tx.v = HexNumber(0)
            signed_tx.r = HexNumber(0)
            signed_tx.s = HexNumber(0)
        case "invalid_s":
            signed_tx.v = HexNumber(signed_tx.v ^ 1)
            signed_tx.s = HexNumber(int(SECP256K1N) - signed_tx.s)
        case _:
            raise ValueError(f"unknown signature type: {signature_type}")

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=[signed_tx],
                expected_inclusion_list_satisfied=expected_satisfied,
            )
        ],
    )


@pytest.mark.parametrize("tx_location", ["prior_block", "same_block"])
def test_unsatisfied_when_block_tx_funds_pending_il_sender(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_location: str,
) -> None:
    """
    A block tx funds the pending IL tx's sender, making it appendable.

    Bob starts with no balance, so its omitted IL tx is only affordable
    once Alice's transfer lands. Funding Bob in the same block additionally
    verifies that FOCIL judges appendability against the post-execution
    state rather than the state the block started from.
    """
    calc = fork.transaction_intrinsic_cost_calculator()
    simple_transfer_gas = calc()
    gas_price = TransactionDefaults.gas_price

    # Bob starts broke; its pending IL tx costs exactly this to run, so
    # Alice's transfer funds it with exactly enough to be appendable.
    bob_il_tx_cost = simple_transfer_gas * gas_price

    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)
    recipient = pre.nonexistent_account()

    alice_tx = Transaction(sender=alice, to=bob, value=bob_il_tx_cost)
    bob_il_tx = Transaction(
        sender=bob, to=recipient, gas_limit=simple_transfer_gas
    )

    blocks: list[Block]
    match tx_location:
        case "prior_block":
            blocks = [
                Block(txs=[alice_tx]),
                Block(
                    txs=[],
                    inclusion_list_txs=[bob_il_tx],
                    expected_inclusion_list_satisfied=False,
                ),
            ]
        case "same_block":
            blocks = [
                Block(
                    txs=[alice_tx],
                    inclusion_list_txs=[bob_il_tx],
                    expected_inclusion_list_satisfied=False,
                )
            ]
        case _:
            raise ValueError(f"unknown tx location: {tx_location}")

    blockchain_test(
        pre=pre,
        post={bob: Account(balance=bob_il_tx_cost)},
        blocks=blocks,
    )


@pytest.mark.parametrize(
    ("authorization_nonce", "pending_il_nonce"),
    [
        pytest.param(0, 0, id="valid_authorization_omits_nonce_zero_il"),
        pytest.param(
            0,
            1,
            id="valid_authorization_requires_nonce_one_il",
        ),
        pytest.param(
            1,
            0,
            id="invalid_authorization_keeps_nonce_zero_il_appendable",
        ),
        pytest.param(
            1,
            1,
            id="invalid_authorization_omits_nonce_one_il",
        ),
    ],
)
def test_pending_il_depends_on_7702_authorization_nonce_effect(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    authorization_nonce: int,
    pending_il_nonce: int,
) -> None:
    """
    EIP-7702 authorization handling changes whether a pending IL tx is valid.

    A valid authorization from Bob increments Bob's nonce during block
    execution, so Bob's pending nonce-0 tx becomes invalid while a nonce-1 tx
    becomes appendable. If the authorization is invalid, Bob's nonce stays at
    0 and the opposite IL outcome applies. Ample block gas keeps the pending
    tx always fitting, so the outcome depends only on Bob's post nonce.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa()
    delegated_contract = pre.deploy_contract(Op.STOP)
    recipient = pre.nonexistent_account()
    bob_recipient = pre.nonexistent_account()

    set_code_tx = Transaction(
        sender=alice,
        to=recipient,
        authorization_list=[
            AuthorizationTuple(
                signer=bob,
                address=delegated_contract,
                nonce=authorization_nonce,
            )
        ],
    )
    bob_il_tx = Transaction(
        sender=bob,
        nonce=pending_il_nonce,
        to=bob_recipient,
        value=1,
    )

    # A valid authorization (nonce matches Bob's current nonce of 0) bumps
    # Bob's nonce to 1. The pending IL tx is appendable only when its nonce
    # matches Bob's resulting nonce.
    bob_post_nonce = 1 if authorization_nonce == 0 else 0
    expected_satisfied = pending_il_nonce != bob_post_nonce
    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[set_code_tx],
                inclusion_list_txs=[bob_il_tx],
                expected_inclusion_list_satisfied=expected_satisfied,
            )
        ],
    )


def test_unsatisfied_with_contract_creating_pending_il_tx(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    A valid, appendable contract-creating pending IL tx is unsatisfied.

    Contract creation exercises the EL's appendability re-validation for a
    `to=None` transaction: the tx is valid and fits, so omitting it from the
    block leaves the payload inclusion-list-unsatisfied.
    """
    sender = pre.fund_eoa()
    create_tx = Transaction(sender=sender, to=None)
    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=[create_tx],
                expected_inclusion_list_satisfied=False,
            )
        ],
    )


@pytest.mark.parametrize(
    "tx_type",
    [
        pytest.param(0, id="legacy"),
        pytest.param(1, id="access_list_2930"),
        pytest.param(2, id="eip1559"),
    ],
)
def test_unsatisfied_with_typed_pending_il_tx(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    tx_type: int,
) -> None:
    """
    An appendable pending IL tx of any non-blob type is unsatisfied.

    The EL re-validates missing IL transactions using normal transaction
    validation, so a valid, appendable transaction makes the block
    INCLUSION_LIST_UNSATISFIED regardless of its type. Blob (type 3) and
    set-code (type 4) transactions have their own dedicated tests.
    """
    sender = pre.fund_eoa()
    recipient = pre.nonexistent_account()

    match tx_type:
        case 1:
            il_tx = Transaction(
                ty=1,
                sender=sender,
                to=recipient,
                value=1,
                access_list=[
                    AccessList(address=recipient, storage_keys=[0x01])
                ],
            )
        case 2:
            il_tx = Transaction(ty=2, sender=sender, to=recipient, value=1)
        case _:
            il_tx = Transaction(ty=0, sender=sender, to=recipient, value=1)

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=[il_tx],
                expected_inclusion_list_satisfied=False,
            )
        ],
    )


def test_block_with_pending_blob_il_tx_is_valid(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Blob transactions in the IL."""
    sender = pre.fund_eoa()
    recipient = pre.nonexistent_account()
    blob_tx = Transaction(
        sender=sender,
        to=recipient,
        max_fee_per_blob_gas=fork.min_base_fee_per_blob_gas(),
        blob_versioned_hashes=add_kzg_version(
            [Hash(1)],
            VERSIONED_HASH_VERSION_KZG[0],
        ),
    )

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=[blob_tx],
                expected_inclusion_list_satisfied=False,
            )
        ],
    )
