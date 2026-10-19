"""
Fork-transition tests for EIP-7976.

EIP-7976 raises the calldata floor price at the Amsterdam fork
boundary: the EIP-7623 floor of 10 gas per token (10/40 per zero or
non-zero byte) becomes 16 gas per floor token with floor tokens counted
uniformly as four per calldata byte (64/64). These tests send identical
data-heavy transactions in a pre-fork block and a post-fork block and
assert that the floor changes exactly at the boundary, both as billed
gas and as the transaction-validity threshold.

The calldata sizes sit above the crossover where the new floor exceeds
the old one: EIP-2780 lowers the floor anchor (the decomposed intrinsic
base) below the flat pre-fork 21_000, so for small calldata the new
floor is the lower of the two even though the per-byte rate rises.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    EIPChecklist,
    RecipientType,
    Transaction,
    TransactionException,
    TransactionReceipt,
    TransitionFork,
)

from .spec import ref_spec_7976

REFERENCE_SPEC_GIT_PATH = ref_spec_7976.git_path
REFERENCE_SPEC_VERSION = ref_spec_7976.version

pytestmark = pytest.mark.valid_at_transition_to("EIP7976")

# Transition forks switch at timestamp 15_000.
PRE_FORK_TIMESTAMP = 14_999
POST_FORK_TIMESTAMP = 15_000

# Calldata shapes sized above the old-floor/new-floor crossover so the
# post-fork floor is strictly larger (see module docstring).
ALL_ZERO_DATA = b"\x00" * 200
ALL_NONZERO_DATA = b"\x01" * 400


def expected_floors(fork: TransitionFork, data: bytes) -> tuple[int, int]:
    """
    Hand-derive the pre- and post-fork calldata floors for `data`.

    Pre-fork (EIP-7623): 10 gas per token, one token per zero byte and
    four per non-zero byte, anchored on the flat `TX_BASE`. Post-fork
    (EIP-7976): 16 gas per token, four tokens per calldata byte
    regardless of content, anchored on the EIP-2780 decomposed base,
    which includes the recipient-access charge for a plain call.
    """
    pre_costs = fork.fork_at(timestamp=PRE_FORK_TIMESTAMP).gas_costs()
    post_costs = fork.fork_at(timestamp=POST_FORK_TIMESTAMP).gas_costs()

    zero_bytes = data.count(0)
    nonzero_bytes = len(data) - zero_bytes

    pre_tokens = zero_bytes + nonzero_bytes * 4
    expected_pre = int(
        pre_costs.TX_BASE + pre_tokens * pre_costs.TX_DATA_TOKEN_FLOOR
    )

    post_floor_tokens = len(data) * int(post_costs.TX_DATA_TOKEN_STANDARD)
    expected_post = int(
        post_costs.TX_BASE
        + post_costs.COLD_ACCOUNT_ACCESS
        + post_floor_tokens * post_costs.TX_DATA_TOKEN_FLOOR
    )

    return expected_pre, expected_post


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
@pytest.mark.parametrize(
    "data",
    [
        pytest.param(ALL_ZERO_DATA, id="all_zero_bytes"),
        pytest.param(ALL_NONZERO_DATA, id="all_nonzero_bytes"),
    ],
)
def test_floor_cost_across_amsterdam_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    data: bytes,
) -> None:
    """
    Pin the EIP-7976 floor increase across the Amsterdam boundary.

    The same data-heavy transaction to an existing EOA (no EVM
    execution) is sent in a pre-fork block and a post-fork block with
    the gas limit pinned to the fork-appropriate floor, so the billed
    gas equals the calldata floor exactly on both sides. The zero-byte
    arm discriminates the uniform token counting (zero bytes lose their
    floor discount); the non-zero arm discriminates the per-token price
    alone.

    The per-fork floor returned by the calculator is also checked
    against a hand-derived value built from each fork's gas constants,
    so a calculator regression fails here with a clear message rather
    than only as a downstream balance mismatch.
    """
    gas_price = 1_000_000_000
    target = pre.fund_eoa(amount=1)

    expected_pre, expected_post = expected_floors(fork, data)

    timestamps = [PRE_FORK_TIMESTAMP, POST_FORK_TIMESTAMP]
    expected_floors_per_block = [expected_pre, expected_post]
    blocks = []
    post: dict[Address, Account] = {}

    for timestamp, expected_floor in zip(
        timestamps, expected_floors_per_block, strict=True
    ):
        sub_fork = fork.fork_at(timestamp=timestamp)
        floor = sub_fork.transaction_data_floor_cost_calculator()(
            data=data,
            recipient_type=RecipientType.EOA,
        )
        assert floor == expected_floor, (
            f"floor at timestamp {timestamp} ({sub_fork}) is {floor}, "
            f"expected {expected_floor}"
        )
        # The floor must dominate the standard-side intrinsic so the
        # transaction is billed exactly the floor.
        intrinsic = sub_fork.transaction_intrinsic_cost_calculator()(
            calldata=data,
            recipient_type=RecipientType.EOA,
            return_cost_deducted_prior_execution=True,
        )
        assert floor > intrinsic, (
            f"floor {floor} does not dominate intrinsic {intrinsic} at "
            f"timestamp {timestamp} ({sub_fork})"
        )

        sender_initial_balance = 10**18
        sender = pre.fund_eoa(sender_initial_balance)

        # The recipient is an EOA, so no EVM bytecode runs and the
        # billed gas is exactly the floor; the gas limit is pinned to
        # the floor, leaving no buffer.
        tx = Transaction(
            sender=sender,
            to=target,
            data=data,
            gas_limit=floor,
            gas_price=gas_price,
            expected_receipt=TransactionReceipt(cumulative_gas_used=floor),
        )
        blocks.append(Block(timestamp=timestamp, txs=[tx]))

        post[sender] = Account(
            nonce=1,
            balance=sender_initial_balance - floor * gas_price,
        )

    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.inclusion_test
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedBeforeFork()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.RejectedBeforeFork()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedAfterFork()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.RejectedAfterFork()
@pytest.mark.parametrize(
    "data",
    [
        pytest.param(ALL_ZERO_DATA, id="all_zero_bytes"),
        pytest.param(ALL_NONZERO_DATA, id="all_nonzero_bytes"),
    ],
)
@pytest.mark.parametrize(
    "scenario",
    [
        pytest.param("exact_floors_accepted", id="exact_floors_accepted"),
        pytest.param(
            "below_old_floor_rejected_before_fork",
            marks=pytest.mark.exception_test,
            id="below_old_floor_rejected_before_fork",
        ),
        pytest.param(
            "old_floor_rejected_after_fork",
            marks=pytest.mark.exception_test,
            id="old_floor_rejected_after_fork",
        ),
        pytest.param(
            "below_new_floor_rejected_after_fork",
            marks=pytest.mark.exception_test,
            id="below_new_floor_rejected_after_fork",
        ),
    ],
)
def test_floor_validity_across_amsterdam_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    scenario: str,
    data: bytes,
) -> None:
    """
    Pin the EIP-7976 validity-threshold change across the boundary.

    The gas limit must reserve the calldata floor for the transaction to
    be valid. A transaction whose gas limit exactly meets the old
    (EIP-7623) floor is accepted in the pre-fork block, but the
    identical shape is rejected once the fork activates because the new
    floor is higher for this calldata; one below the old floor is
    already rejected pre-fork, one just below the new floor is rejected
    post-fork, and one at the new floor is accepted post-fork.

    The zero-byte arm pins the uniform token counting on the validity
    threshold itself, independently of the billed-gas path.
    """
    gas_price = 1_000_000_000
    target = pre.fund_eoa(amount=1)

    old_floor, new_floor = expected_floors(fork, data)
    # The old-floor-rejected-after-fork arm only exists because the new
    # floor exceeds the old one for this calldata size.
    assert new_floor > old_floor

    below_floor_error = TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST
    sender_initial_balance = 10**18
    pre_fork_sender = pre.fund_eoa(sender_initial_balance)
    post_fork_sender = pre.fund_eoa(sender_initial_balance)

    def transfer_tx(
        sender: Address, gas_limit: int, valid: bool
    ) -> Transaction:
        return Transaction(
            sender=sender,
            to=target,
            data=data,
            gas_limit=gas_limit,
            gas_price=gas_price,
            error=None if valid else below_floor_error,
        )

    untouched = Account(nonce=0, balance=sender_initial_balance)
    blocks: list[Block]

    if scenario == "exact_floors_accepted":
        blocks = [
            Block(
                timestamp=PRE_FORK_TIMESTAMP,
                txs=[transfer_tx(pre_fork_sender, old_floor, valid=True)],
            ),
            Block(
                timestamp=POST_FORK_TIMESTAMP,
                txs=[transfer_tx(post_fork_sender, new_floor, valid=True)],
            ),
        ]
        post = {
            pre_fork_sender: Account(
                nonce=1,
                balance=sender_initial_balance - old_floor * gas_price,
            ),
            post_fork_sender: Account(
                nonce=1,
                balance=sender_initial_balance - new_floor * gas_price,
            ),
        }
    elif scenario == "below_old_floor_rejected_before_fork":
        blocks = [
            Block(
                timestamp=PRE_FORK_TIMESTAMP,
                txs=[transfer_tx(pre_fork_sender, old_floor - 1, valid=False)],
                exception=below_floor_error,
            ),
        ]
        post = {pre_fork_sender: untouched, post_fork_sender: untouched}
    elif scenario == "old_floor_rejected_after_fork":
        blocks = [
            Block(
                timestamp=PRE_FORK_TIMESTAMP,
                txs=[transfer_tx(pre_fork_sender, old_floor, valid=True)],
            ),
            # The identical gas limit that was accepted pre-fork no
            # longer reserves the raised floor.
            Block(
                timestamp=POST_FORK_TIMESTAMP,
                txs=[transfer_tx(post_fork_sender, old_floor, valid=False)],
                exception=below_floor_error,
            ),
        ]
        post = {
            pre_fork_sender: Account(
                nonce=1,
                balance=sender_initial_balance - old_floor * gas_price,
            ),
            post_fork_sender: untouched,
        }
    else:
        # One below the new floor is still rejected post-fork; together
        # with the exact-floor acceptance this pins the post-fork
        # threshold at exactly the new floor.
        blocks = [
            Block(
                timestamp=POST_FORK_TIMESTAMP,
                txs=[
                    transfer_tx(post_fork_sender, new_floor - 1, valid=False)
                ],
                exception=below_floor_error,
            ),
        ]
        post = {pre_fork_sender: untouched, post_fork_sender: untouched}

    blockchain_test(pre=pre, blocks=blocks, post=post)
