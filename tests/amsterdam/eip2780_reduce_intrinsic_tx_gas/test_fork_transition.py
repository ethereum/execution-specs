"""
Fork-transition tests for EIP-2780.

EIP-2780 reshapes the intrinsic transaction cost at the Amsterdam fork
boundary. These tests send identical transactions in a pre-fork block
and a post-fork block (straddling the transition timestamp) and assert
that the per-transaction gas paid changes by the EIP-2780 amount only
once the fork activates.

For these shapes the post-fork intrinsic decomposes from the flat
pre-fork ``TX_BASE`` of 21_000 as follows:

- A plain call to an existing account drops to ``TX_BASE`` (12_000)
  plus the new ``COLD_ACCOUNT_ACCESS`` recipient charge; adding value
  re-raises it to exactly 21_000 (the value-transfer cost is invariant
  across the fork by design).
- A self-transfer is fully carved out post-fork: it pays only the
  lowered ``TX_BASE`` with no recipient or value-transfer charge,
  regardless of value, the largest reduction.
- A contract creation splits the flat pre-fork ``TX_CREATE`` into the
  ``CREATE_ACCESS`` execution intrinsic and a top-frame ``NEW_ACCOUNT``
  state charge.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Op,
    RecipientType,
    Transaction,
    TransactionReceipt,
    TransitionFork,
    compute_create_address,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .helpers import EOA_INITIAL_BALANCE
from .spec import ref_spec_2780

REFERENCE_SPEC_GIT_PATH = ref_spec_2780.git_path
REFERENCE_SPEC_VERSION = ref_spec_2780.version

pytestmark = pytest.mark.valid_at_transition_to("Amsterdam")

# Transition forks switch at timestamp 15_000.
PRE_FORK_TIMESTAMP = 14_999
POST_FORK_TIMESTAMP = 15_000


@pytest.mark.parametrize(
    "self_transfer",
    [
        pytest.param(False, id="plain_call"),
        pytest.param(True, id="self_transfer"),
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_intrinsic_reduction_across_amsterdam_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    self_transfer: bool,
    value: int,
) -> None:
    """
    Pin the EIP-2780 intrinsic change across the Amsterdam boundary.

    The same transaction shape is sent in a pre-fork block (Osaka
    rules, flat 21_000 intrinsic) and a post-fork block (Amsterdam
    rules, decomposed intrinsic). Each block uses a distinct sender so
    its post-tx balance pins the fork-appropriate intrinsic; the
    recipient is an existing EOA (or the sender itself for
    ``self_transfer``), so neither block runs EVM bytecode and
    ``gas_used`` equals the intrinsic exactly.

    The per-fork intrinsic returned by the calculator is also checked
    against a hand-derived decomposition built from each fork's gas
    constants, so a calculator regression fails here with a clear
    message rather than only as a downstream balance mismatch.
    """
    gas_price = 1_000_000_000
    recipient_type = RecipientType.SELF if self_transfer else RecipientType.EOA

    pre_fork = fork.fork_at(timestamp=PRE_FORK_TIMESTAMP)
    post_fork = fork.fork_at(timestamp=POST_FORK_TIMESTAMP)

    # Pre-fork: flat ``TX_BASE`` regardless of recipient kind or value.
    expected_pre = pre_fork.gas_costs().TX_BASE
    # Post-fork: EIP-2780 decomposition. Self-transfers are fully
    # carved out; other recipients pay the recipient access charge plus
    # the value-transfer charges when value is moved.
    post_gas_costs = post_fork.gas_costs()
    expected_post = post_gas_costs.TX_BASE
    if not self_transfer:
        expected_post += post_gas_costs.COLD_ACCOUNT_ACCESS
        if value:
            expected_post += post_gas_costs.TX_VALUE_COST

    timestamps = [PRE_FORK_TIMESTAMP, POST_FORK_TIMESTAMP]
    expected_intrinsics = [expected_pre, expected_post]
    blocks = []
    post: dict[Address, Account] = {}

    for timestamp, expected_intrinsic in zip(
        timestamps, expected_intrinsics, strict=True
    ):
        sub_fork = fork.fork_at(timestamp=timestamp)
        intrinsic_gas = sub_fork.transaction_intrinsic_cost_calculator()(
            sends_value=bool(value),
            recipient_type=recipient_type,
            return_cost_deducted_prior_execution=True,
        )
        assert intrinsic_gas == expected_intrinsic, (
            f"intrinsic at timestamp {timestamp} ({sub_fork}) is "
            f"{intrinsic_gas}, expected {expected_intrinsic}"
        )

        sender_initial_balance = 10**18
        sender = pre.fund_eoa(sender_initial_balance)
        if self_transfer:
            target = sender
        else:
            target = pre.fund_eoa(amount=EOA_INITIAL_BALANCE)

        # No EVM bytecode runs (recipient is an EOA or the sender), so
        # gas_used == intrinsic_gas; the gas limit is pinned to exactly
        # the intrinsic, leaving no buffer.
        tx = Transaction(
            sender=sender,
            to=target,
            value=value,
            gas_limit=intrinsic_gas,
            gas_price=gas_price,
        )
        blocks.append(Block(timestamp=timestamp, txs=[tx]))

        # A self-transfer returns the value to the sender (net zero);
        # a plain call moves ``value`` to the distinct recipient.
        sender_value_delta = 0 if self_transfer else value
        sender_final_balance = (
            sender_initial_balance
            - sender_value_delta
            - intrinsic_gas * gas_price
        )
        post[sender] = Account(nonce=1, balance=sender_final_balance)
        if not self_transfer:
            post[target] = Account(balance=EOA_INITIAL_BALANCE + value)

    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_creation_tx_intrinsic_across_amsterdam_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    value: int,
) -> None:
    """
    Pin the EIP-2780 creation-transaction change across the Amsterdam
    boundary.

    The same creation transaction (``to=None``, ``STOP`` init code that
    deploys empty code) is sent in a pre-fork block and a post-fork
    block, each from a fresh sender with the gas limit pinned exactly.
    Pre-fork the whole cost is execution intrinsic: ``TX_BASE`` plus the
    flat ``TX_CREATE``. Post-fork the intrinsic keeps only the
    ``CREATE_ACCESS`` execution portion of ``TX_CREATE``, while the created
    account's ``NEW_ACCOUNT`` is charged as *state* gas at the top frame — the
    sender-facing total is the sum of both.

    The per-fork costs are hand-derived from each fork's gas constants
    and checked against the calculators, so a calculator regression
    fails with a clear message rather than only as a downstream balance
    mismatch.
    """
    gas_price = 1_000_000_000
    init_code = Op.STOP

    pre_fork = fork.fork_at(timestamp=PRE_FORK_TIMESTAMP)
    post_fork = fork.fork_at(timestamp=POST_FORK_TIMESTAMP)
    pre_costs = pre_fork.gas_costs()
    post_costs = post_fork.gas_costs()

    # Shared calldata terms for the one-byte STOP init code: a single
    # zero-byte token, plus the EIP-3860 metering of one 32-byte init
    # code word at 2 gas. Identical on both sides of the fork.
    assert (
        post_costs.TX_DATA_TOKEN_STANDARD == pre_costs.TX_DATA_TOKEN_STANDARD
    )
    init_code_terms = pre_costs.TX_DATA_TOKEN_STANDARD + 2

    # Pre-fork: flat execution intrinsic, no top-frame charge.
    expected_pre = pre_costs.TX_BASE + pre_costs.TX_CREATE + init_code_terms
    # Post-fork: EIP-8037 folds ``NEW_ACCOUNT`` into ``TX_CREATE``;
    # EIP-2780 moves that state portion to the top frame, leaving the
    # ``CREATE_ACCESS`` execution remainder in the intrinsic.
    expected_post = (
        post_costs.TX_BASE
        + (post_costs.TX_CREATE - post_costs.NEW_ACCOUNT)
        + init_code_terms
    )
    expected_post_state = post_costs.NEW_ACCOUNT

    timestamps = [PRE_FORK_TIMESTAMP, POST_FORK_TIMESTAMP]
    expected_intrinsics = [expected_pre, expected_post]
    expected_top_frame_states = [0, expected_post_state]
    blocks = []
    post: dict[Address, Account] = {}

    for timestamp, expected_intrinsic, expected_state in zip(
        timestamps, expected_intrinsics, expected_top_frame_states, strict=True
    ):
        sub_fork = fork.fork_at(timestamp=timestamp)
        intrinsic_gas = sub_fork.transaction_intrinsic_cost_calculator()(
            calldata=init_code,
            contract_creation=True,
            sends_value=bool(value),
            return_cost_deducted_prior_execution=True,
        )
        assert intrinsic_gas == expected_intrinsic, (
            f"creation intrinsic at timestamp {timestamp} ({sub_fork}) is "
            f"{intrinsic_gas}, expected {expected_intrinsic}"
        )
        top_frame_state_gas = sub_fork.transaction_top_frame_state_gas(
            contract_creation=True,
        )
        assert top_frame_state_gas == expected_state, (
            f"top-frame state gas at timestamp {timestamp} ({sub_fork}) is "
            f"{top_frame_state_gas}, expected {expected_state}"
        )

        sender_initial_balance = 10**18
        sender = pre.fund_eoa(sender_initial_balance)
        created = compute_create_address(address=sender, nonce=sender.nonce)

        # The STOP init code costs no execution gas and deploys empty
        # code (no deposit charges), so the gas limit is pinned to
        # exactly the intrinsic plus the fork's top-frame state charge.
        total_gas = intrinsic_gas + top_frame_state_gas
        tx = Transaction(
            sender=sender,
            to=None,
            data=init_code,
            value=value,
            gas_limit=total_gas,
            gas_price=gas_price,
        )
        blocks.append(Block(timestamp=timestamp, txs=[tx]))

        post[sender] = Account(
            nonce=1,
            balance=sender_initial_balance - value - total_gas * gas_price,
        )
        post[created] = Account(nonce=1, balance=value, code=b"")

    blockchain_test(pre=pre, blocks=blocks, post=post)


def test_setcode_tx_across_amsterdam_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
) -> None:
    """
    Pin the EIP-2780 authorization repricing across the Amsterdam
    boundary.
    """
    gas_price = 1_000_000_000

    pre_costs = fork.fork_at(timestamp=PRE_FORK_TIMESTAMP).gas_costs()
    post_costs = fork.fork_at(timestamp=POST_FORK_TIMESTAMP).gas_costs()

    # Pre-fork: EIP-7702 charges the full per-authorization cost in the
    # intrinsic; an empty authority earns no existing-authority refund.
    expected_pre = pre_costs.TX_BASE + pre_costs.AUTH_PER_EMPTY_ACCOUNT
    # Post-fork: EIP-2780 decomposition across the three charge layers.
    expected_post = (
        post_costs.TX_BASE
        + post_costs.COLD_ACCOUNT_ACCESS
        + post_costs.EXECUTION_PER_AUTH_BASE_COST
        + post_costs.ACCOUNT_WRITE
        + post_costs.NEW_ACCOUNT
        + post_costs.AUTH_BASE
    )

    timestamps = [PRE_FORK_TIMESTAMP, POST_FORK_TIMESTAMP]
    expected_totals = [expected_pre, expected_post]
    blocks = []
    post: dict[Address, Account] = {}

    for timestamp, expected_total in zip(
        timestamps, expected_totals, strict=True
    ):
        sub_fork = fork.fork_at(timestamp=timestamp)
        recipient = pre.deploy_contract(code=Op.STOP)
        delegate_to = pre.deploy_contract(code=Op.STOP)
        authority = pre.fund_eoa(amount=0)
        authorization = AuthorizationTuple(
            address=delegate_to,
            nonce=0,
            signer=authority,
            creates_account=True,
        )

        intrinsic_gas = sub_fork.transaction_intrinsic_cost_calculator()(
            recipient_type=RecipientType.CONTRACT,
            authorization_list_or_count=[authorization],
            return_cost_deducted_prior_execution=True,
        )
        top_frame_gas = sub_fork.transaction_top_frame_execution_gas(
            recipient_type=RecipientType.CONTRACT,
            authorizations=[authorization],
        )
        top_frame_state_gas = sub_fork.transaction_top_frame_state_gas(
            recipient_type=RecipientType.CONTRACT,
            authorizations=[authorization],
        )
        total_gas = intrinsic_gas + top_frame_gas + top_frame_state_gas
        assert total_gas == expected_total, (
            f"set-code total at timestamp {timestamp} ({sub_fork}) is "
            f"{total_gas}, expected {expected_total}"
        )

        sender_initial_balance = 10**18
        sender = pre.fund_eoa(sender_initial_balance)

        # Both recipient and delegate run ``STOP`` (no execution gas),
        # so the receipt pins the intrinsic and top-frame layers alone.
        tx = Transaction(
            sender=sender,
            to=recipient,
            authorization_list=[authorization],
            gas_limit=total_gas,
            max_fee_per_gas=gas_price,
            max_priority_fee_per_gas=gas_price,
            expected_receipt=TransactionReceipt(
                cumulative_gas_used=total_gas,
            ),
        )
        blocks.append(Block(timestamp=timestamp, txs=[tx]))

        post[sender] = Account(
            nonce=1,
            balance=sender_initial_balance - total_gas * gas_price,
        )
        post[authority] = Account(
            nonce=1,
            balance=0,
            code=Spec7702.delegation_designation(delegate_to),
        )

    blockchain_test(pre=pre, blocks=blocks, post=post)
