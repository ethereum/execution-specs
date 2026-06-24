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
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    RecipientType,
    Transaction,
    TransitionFork,
)

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
    gas_price = 10**9
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
            expected_post += (
                post_gas_costs.TRANSFER_LOG_COST + post_gas_costs.TX_VALUE_COST
            )

    timestamps = [PRE_FORK_TIMESTAMP, POST_FORK_TIMESTAMP]
    expected_intrinsics = [expected_pre, expected_post]
    blocks = []
    post: dict = {}

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
