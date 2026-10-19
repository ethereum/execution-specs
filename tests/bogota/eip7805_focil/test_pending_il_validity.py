"""Tests EIP-7805 FOCIL appendability of omitted IL txs by tx validity."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    ChainConfig,
    Environment,
    Fork,
    Hash,
    Header,
    Op,
    SystemCallPhase,
    Transaction,
    TransactionType,
    Withdrawal,
    add_kzg_version,
)
from execution_testing.base_types import HexNumber
from execution_testing.test_types.transaction_types import (
    TransactionDefaults,
)

from ethereum.crypto.elliptic_curve import SECP256K1N
from ethereum.forks.bogota.transactions import VERSIONED_HASH_VERSION_KZG

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
        "fee_cap_exactly_affordable",
        "fee_cap_one_wei_short",
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
    only on whether the sender's balance covers the gas limit at the fee cap
    plus the value. The calldata case shows a single non-zero byte lifting the
    cost just past an otherwise-sufficient balance.
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

    # The balance must cover the fee cap, not the lower price the block would
    # charge. The one-wei-short side tells the two apart only because the
    # block's base fee is below the cap: the affordable case shows a legacy
    # transaction at a tenth of the cap is valid in this block.
    fee_cap = 10 * gas_price
    fee_cap_value = 1
    value_transfer_gas = calc(sends_value=True)
    fee_cap_cost = value_transfer_gas * fee_cap + fee_cap_value

    def fee_cap_tx(*, balance: int) -> Transaction:
        return Transaction(
            ty=2,
            sender=pre.fund_eoa(amount=balance),
            to=recipient,
            gas_limit=value_transfer_gas,
            max_fee_per_gas=fee_cap,
            max_priority_fee_per_gas=0,
            value=fee_cap_value,
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
        case "fee_cap_exactly_affordable":
            pending = [fee_cap_tx(balance=fee_cap_cost)]
            expected_satisfied = False
        case "fee_cap_one_wei_short":
            pending = [fee_cap_tx(balance=fee_cap_cost - 1)]
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


def set_code_authorization(pre: Alloc) -> AuthorizationTuple:
    """Return an authorization for a pending type-4 IL tx to carry."""
    return AuthorizationTuple(
        signer=pre.fund_eoa(),
        address=pre.deploy_contract(Op.STOP),
        nonce=0,
    )


def flipped_parity(tx_type: int, v: int) -> int:
    """Return the `v` that recovers with the other parity of the same r."""
    if tx_type == 0:
        # EIP-155: v = 35 + 2 * chain_id + parity. Flipping the low bit of
        # v would change the chain id instead.
        return v + 1 if (v - 35) % 2 == 0 else v - 1
    return v ^ 1


# Smallest r whose x^3 + 7 has no square root mod p, so no curve point has
# it as its x-coordinate.
R_NOT_ON_CURVE = 5

SIGNATURE_CASES = [
    "valid",
    "all_zeros",
    "r_zero",
    "r_equals_n",
    "r_not_on_curve",
    "s_zero",
    "high_s",
    "y_parity_2",
]


@pytest.mark.parametrize(
    "tx_type,signature_type",
    [
        pytest.param(tx_type, case, id=f"type_{tx_type}-{case}")
        for tx_type in (0, 1, 2, 4)
        for case in SIGNATURE_CASES
        # A legacy tx has no y_parity; its v also carries the chain id.
        if not (tx_type == 0 and case == "y_parity_2")
    ],
)
def test_block_with_invalid_signature_pending_il_tx_is_valid(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    tx_type: int,
    signature_type: str,
) -> None:
    """
    A pending IL tx with an invalid signature may be omitted.

    FOCIL reuses normal transaction validation for missing IL transactions.
    If the signature is invalid, the tx is not appendable and omission is
    allowed. Each case breaks one signature check while keeping `v` valid
    for this chain, so the chain id check doesn't skip the tx first. The
    `all_zeros` case on a legacy tx is the exception: its `v` of 0 fails
    the chain id check, not the signature checks.
    """
    authorization_list = (
        [set_code_authorization(pre)] if tx_type == 4 else None
    )
    signed_tx = Transaction(
        ty=tx_type,
        sender=pre.fund_eoa(),
        to=pre.nonexistent_account(),
        gas_limit=100_000,
        authorization_list=authorization_list,
    ).with_signature_and_sender()
    expected_satisfied = True
    match signature_type:
        case "valid":
            expected_satisfied = False
        case "all_zeros":
            signed_tx.v = HexNumber(0)
            signed_tx.r = HexNumber(0)
            signed_tx.s = HexNumber(0)
        case "r_zero":
            signed_tx.r = HexNumber(0)
        case "r_equals_n":
            signed_tx.r = HexNumber(int(SECP256K1N))
        case "r_not_on_curve":
            signed_tx.r = HexNumber(R_NOT_ON_CURVE)
        case "s_zero":
            signed_tx.s = HexNumber(0)
        case "high_s":
            # The same signature with s mirrored and the parity flipped
            # still recovers the sender, so only the low-s rule rejects it.
            signed_tx.v = HexNumber(flipped_parity(tx_type, signed_tx.v))
            signed_tx.s = HexNumber(int(SECP256K1N) - signed_tx.s)
        case "y_parity_2":
            # Keep the low bit, so a client that reads only `v & 1`
            # recovers the funded sender and includes the tx.
            signed_tx.v = HexNumber(signed_tx.v + 2)
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


@pytest.mark.parametrize("withdrawal_block", ["prior_block", "same_block"])
def test_pending_il_sender_funded_by_withdrawal(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    withdrawal_block: str,
) -> None:
    """
    The IL check runs before the block's withdrawals, so a withdrawal funds a
    pending IL tx's sender only from the next block on.
    """
    simple_transfer_gas = fork.transaction_intrinsic_cost_calculator()()
    bob = pre.fund_eoa(amount=0)
    withdrawal_gwei = 1
    assert (
        simple_transfer_gas * TransactionDefaults.gas_price
        <= withdrawal_gwei * 10**9
    )
    withdrawal = Withdrawal(
        index=0, validator_index=0, address=bob, amount=withdrawal_gwei
    )
    bob_il_tx = Transaction(
        sender=bob,
        to=pre.nonexistent_account(),
        gas_limit=simple_transfer_gas,
    )

    match withdrawal_block:
        case "prior_block":
            blocks = [
                Block(withdrawals=[withdrawal]),
                Block(
                    txs=[],
                    inclusion_list_txs=[bob_il_tx],
                    expected_inclusion_list_satisfied=False,
                ),
            ]
        case "same_block":
            blocks = [
                Block(
                    withdrawals=[withdrawal],
                    inclusion_list_txs=[bob_il_tx],
                    expected_inclusion_list_satisfied=True,
                )
            ]
        case _:
            raise ValueError(f"unknown withdrawal block: {withdrawal_block}")

    blockchain_test(
        pre=pre,
        post={bob: Account(balance=withdrawal_gwei * 10**9)},
        blocks=blocks,
    )


@pytest.mark.with_all_system_contracts
@pytest.mark.pre_alloc_mutable
def test_pending_il_sender_funded_by_system_call(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    system_contract: Address,
) -> None:
    """
    The IL check runs after the system calls made before the block's
    transactions and before those made after them, so a system contract that
    funds a pending IL tx's sender makes it appendable only in the first case.
    """
    phase = fork.system_contract_call_phases()[system_contract]
    match phase:
        case SystemCallPhase.BEFORE_TRANSACTIONS:
            expected_satisfied = False
        case SystemCallPhase.AFTER_TRANSACTIONS:
            expected_satisfied = True
        case SystemCallPhase.NONE:
            pytest.skip("the block never calls this system contract")
        case _:
            raise ValueError(f"unknown system call phase: {phase}")

    simple_transfer_gas = fork.transaction_intrinsic_cost_calculator()()
    bob_il_tx_cost = simple_transfer_gas * TransactionDefaults.gas_price
    bob = pre.fund_eoa(amount=0)
    bob_il_tx = Transaction(
        sender=bob,
        to=pre.nonexistent_account(),
        gas_limit=simple_transfer_gas,
    )
    # The system call sends Bob exactly what his IL tx costs.
    pre[system_contract] = Account(
        code=Op.CALL(address=bob, value=bob_il_tx_cost),
        balance=bob_il_tx_cost,
    )

    blockchain_test(
        pre=pre,
        post={
            bob: Account(balance=bob_il_tx_cost),
            system_contract: Account(balance=0),
        },
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=[bob_il_tx],
                expected_inclusion_list_satisfied=expected_satisfied,
            )
        ],
    )


@pytest.mark.parametrize(
    "one_wei_short", [False, True], ids=["exact", "one_wei_short"]
)
def test_pending_il_appendability_by_fee_recipient_earnings(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    one_wei_short: bool,
) -> None:
    """
    Priority fees from the block's transactions fund the fee recipient's
    pending IL tx, since the check runs after they are paid.
    """
    calc = fork.transaction_intrinsic_cost_calculator()
    simple_transfer_gas = calc()
    value_transfer_gas = calc(sends_value=True)
    gas_price = TransactionDefaults.gas_price
    fee_recipient = pre.fund_eoa(amount=0)
    recipient = pre.nonexistent_account()

    # The base fee is at most the default gas price, so the tip is paid in
    # full and the fee recipient earns exactly this.
    tip = 2 * gas_price
    earnings = simple_transfer_gas * tip
    tipping_tx = Transaction(
        ty=2,
        sender=pre.fund_eoa(),
        to=recipient,
        gas_limit=simple_transfer_gas,
        max_fee_per_gas=gas_price + tip,
        max_priority_fee_per_gas=tip,
    )
    # The pending tx's value takes whatever its gas leaves of the earnings.
    affordable_value = earnings - value_transfer_gas * gas_price
    assert affordable_value > 0
    if one_wei_short:
        il_tx_value = affordable_value + 1
        expected_satisfied = True
    else:
        il_tx_value = affordable_value
        expected_satisfied = False
    il_tx = Transaction(
        sender=fee_recipient,
        to=recipient,
        gas_limit=value_transfer_gas,
        value=il_tx_value,
    )

    blockchain_test(
        pre=pre,
        post={fee_recipient: Account(balance=earnings)},
        blocks=[
            Block(
                fee_recipient=fee_recipient,
                txs=[tipping_tx],
                inclusion_list_txs=[il_tx],
                expected_inclusion_list_satisfied=expected_satisfied,
            )
        ],
    )


@pytest.mark.parametrize("drained", [False, True], ids=["funded", "drained"])
def test_pending_il_appendability_after_sender_drained(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    drained: bool,
) -> None:
    """
    A block tx that takes one wei from a delegated sender funded with exactly
    its pending IL tx's cost, leaving its nonce alone, makes that tx
    unaffordable.
    """
    simple_transfer_gas = fork.transaction_intrinsic_cost_calculator()()
    il_tx_cost = simple_transfer_gas * TransactionDefaults.gas_price
    sink = pre.nonexistent_account()
    drainer = pre.deploy_contract(
        code=Op.CALL(gas=Op.GAS, address=sink, value=1)
    )
    sender = pre.fund_eoa(amount=il_tx_cost, delegation=drainer)
    il_tx = Transaction(
        sender=sender,
        to=pre.nonexistent_account(),
        gas_limit=simple_transfer_gas,
    )

    post: dict[Address, Account | None]
    if drained:
        txs = [Transaction(sender=pre.fund_eoa(), to=sender)]
        post = {
            sender: Account(balance=il_tx_cost - 1),
            sink: Account(balance=1),
        }
        expected_satisfied = True
    else:
        txs = []
        post = {sender: Account(balance=il_tx_cost), sink: Account.NONEXISTENT}
        expected_satisfied = False

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[
            Block(
                txs=txs,
                inclusion_list_txs=[il_tx],
                expected_inclusion_list_satisfied=expected_satisfied,
            )
        ],
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


@pytest.mark.with_all_typed_transactions(
    selector=lambda tx_type: tx_type != TransactionType.BLOB_TRANSACTION
)
def test_unsatisfied_with_typed_pending_il_tx(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    typed_transaction: Transaction,
) -> None:
    """An appendable pending IL tx of any non-blob type is unsatisfied."""
    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=[typed_transaction],
                expected_inclusion_list_satisfied=False,
            )
        ],
    )


@pytest.mark.parametrize(
    "blob_tx_in_block", [False, True], ids=["omitted", "included"]
)
@pytest.mark.parametrize(
    "appendable_tx_follows",
    [
        pytest.param(False, id="alone"),
        pytest.param(True, id="before_appendable_tx"),
    ],
)
def test_block_with_pending_blob_il_tx_is_valid(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    blob_tx_in_block: bool,
    appendable_tx_follows: bool,
) -> None:
    """
    The IL check skips blob transactions, so a payload that leaves out an
    otherwise appendable one stays satisfied, and the check goes on to the
    entries after it.
    """
    blob_tx = Transaction(
        sender=pre.fund_eoa(),
        to=pre.nonexistent_account(),
        max_fee_per_blob_gas=fork.min_base_fee_per_blob_gas(),
        blob_versioned_hashes=add_kzg_version(
            [Hash(1)],
            VERSIONED_HASH_VERSION_KZG[0],
        ),
    )
    inclusion_list = [blob_tx]
    if appendable_tx_follows:
        inclusion_list.append(
            Transaction(sender=pre.fund_eoa(), to=pre.nonexistent_account())
        )

    # The included case is the control: the block accepts the blob tx, so
    # the omitted one would have been appendable.
    if blob_tx_in_block:
        block_txs = [blob_tx]
    else:
        block_txs = []

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=block_txs,
                inclusion_list_txs=inclusion_list,
                expected_inclusion_list_satisfied=not appendable_tx_follows,
            )
        ],
    )


@pytest.mark.parametrize(
    "tx_type,chain",
    [
        pytest.param(0, "this_chain", id="legacy_this_chain"),
        pytest.param(0, "other_chain", id="legacy_other_chain"),
        pytest.param(0, "unprotected", id="legacy_unprotected"),
        pytest.param(0, "chain_id_plus_2_64", id="legacy_chain_id_plus_2_64"),
        pytest.param(2, "this_chain", id="type_2_this_chain"),
        pytest.param(2, "other_chain", id="type_2_other_chain"),
    ],
)
@pytest.mark.parametrize(
    "appendable_tx_follows",
    [
        pytest.param(False, id="alone"),
        pytest.param(True, id="before_appendable_tx"),
    ],
)
def test_pending_il_appendability_by_chain_id(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    chain_config: ChainConfig,
    tx_type: int,
    chain: str,
    appendable_tx_follows: bool,
) -> None:
    """
    A pending IL tx signed for another chain, or a legacy tx whose v encodes
    a chain id too large for 64 bits, is skipped, and the check goes on to
    the entries after it. A legacy tx without a chain id counts.
    """
    pending_tx = Transaction(
        ty=tx_type, sender=pre.fund_eoa(), to=pre.nonexistent_account()
    )
    match chain:
        case "this_chain":
            pending_tx = pending_tx.copy(chain_id=chain_config.chain_id)
            entry_counts = True
        case "other_chain":
            pending_tx = pending_tx.copy(chain_id=chain_config.chain_id + 1)
            entry_counts = False
        case "unprotected":
            pending_tx = pending_tx.copy(protected=False)
            entry_counts = True
        case "chain_id_plus_2_64":
            signed_tx = pending_tx.copy(
                chain_id=chain_config.chain_id,
                # Signing up front needs the final gas limit.
                gas_limit=fork.transaction_intrinsic_cost_calculator()(),
            ).with_signature_and_sender()
            # EIP-155: v = 35 + 2 * chain_id + parity. The chain id's low 64
            # bits are still this chain's, so truncating it counts the entry.
            pending_tx = signed_tx.copy(v=signed_tx.v + 2 * 2**64)
            entry_counts = False
        case _:
            raise ValueError(f"unknown chain: {chain}")

    inclusion_list = [pending_tx]
    if appendable_tx_follows:
        inclusion_list.append(
            Transaction(sender=pre.fund_eoa(), to=pre.nonexistent_account())
        )

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=inclusion_list,
                expected_inclusion_list_satisfied=not (
                    entry_counts or appendable_tx_follows
                ),
            )
        ],
    )


@pytest.mark.parametrize(
    "tx_type",
    [
        pytest.param(0, id="legacy_gas_price"),
        pytest.param(1, id="access_list_gas_price"),
        pytest.param(2, id="eip1559_max_fee"),
        pytest.param(4, id="set_code_max_fee"),
    ],
)
@pytest.mark.parametrize("fee_cap", ["base_fee", "one_wei_below_base_fee"])
def test_pending_il_appendability_by_base_fee(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    fee_cap: str,
) -> None:
    """A pending IL tx whose fee cap is below the base fee may be omitted."""
    # The default genesis base fee is too small to move after an empty block,
    # so clients that update it under EIP-8198 agree on it too.
    genesis_environment = Environment().set_fork_requirements(fork)
    assert genesis_environment.base_fee_per_gas is not None
    base_fee_per_gas = fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=int(genesis_environment.base_fee_per_gas),
        parent_gas_used=0,
        parent_gas_limit=genesis_environment.gas_limit,
    )
    match fee_cap:
        case "base_fee":
            max_fee = base_fee_per_gas
            expected_satisfied = False
        case "one_wei_below_base_fee":
            max_fee = base_fee_per_gas - 1
            expected_satisfied = True
        case _:
            raise ValueError(f"unknown fee cap: {fee_cap}")

    match tx_type:
        case 0 | 1:
            pending_tx = Transaction(
                ty=tx_type,
                sender=pre.fund_eoa(),
                to=pre.nonexistent_account(),
                gas_price=max_fee,
            )
        case 2 | 4:
            pending_tx = Transaction(
                ty=tx_type,
                sender=pre.fund_eoa(),
                to=pre.nonexistent_account(),
                max_fee_per_gas=max_fee,
                max_priority_fee_per_gas=0,
                authorization_list=(
                    [set_code_authorization(pre)] if tx_type == 4 else None
                ),
            )
        case _:
            raise ValueError(f"unknown tx type: {tx_type}")

    blockchain_test(
        genesis_environment=genesis_environment,
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=[pending_tx],
                expected_inclusion_list_satisfied=expected_satisfied,
                header_verify=Header(base_fee_per_gas=base_fee_per_gas),
            )
        ],
    )


@pytest.mark.parametrize(
    "sender_code",
    [
        "delegation",
        pytest.param("contract", marks=pytest.mark.pre_alloc_mutable),
    ],
)
def test_pending_il_appendability_by_sender_code(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    sender_code: str,
) -> None:
    """
    A pending IL tx from a sender with code may be omitted unless the code
    is an EIP-7702 delegation.
    """
    match sender_code:
        case "delegation":
            sender = pre.fund_eoa(delegation=pre.deploy_contract(Op.STOP))
            expected_satisfied = False
        case "contract":
            sender = pre.fund_eoa(code=Op.STOP)
            expected_satisfied = True
        case _:
            raise ValueError(f"unknown sender code: {sender_code}")

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=[
                    Transaction(sender=sender, to=pre.nonexistent_account())
                ],
                expected_inclusion_list_satisfied=expected_satisfied,
            )
        ],
    )
