"""
Fork-transition tests for [EIP-7981: Increase Access List Cost](https://eips.ethereum.org/EIPS/eip-7981).

EIP-7981 adds a data-footprint surcharge for access list bytes at the
Amsterdam fork boundary. These tests send identical access-list
transactions in a pre-fork block and a post-fork block (straddling the
transition timestamp) and pin the per-transaction gas paid on each side,
plus the validity flip for gas limits inside the uplift gap.

The post-fork intrinsic composes three repricings; the hand-derived
expectations below keep each term explicit so the EIP-7981 surcharge is
individually visible:

- EIP-2780 decomposes the flat pre-fork `TX_BASE` into the lowered base
  plus the `COLD_ACCOUNT_ACCESS` recipient charge.
- EIP-8038 reprices the per-address and per-storage-key access list
  charges to the fork's cold access costs.
- EIP-7981 adds four floor tokens per access list byte, charged at
  `TX_DATA_TOKEN_FLOOR` in the intrinsic and counted in the floor.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    EIPChecklist,
    Hash,
    Transaction,
    TransactionException,
    TransactionReceipt,
    TransitionFork,
)

from .helpers import calculate_access_list_floor_tokens
from .spec import ref_spec_7981

REFERENCE_SPEC_GIT_PATH = ref_spec_7981.git_path
REFERENCE_SPEC_VERSION = ref_spec_7981.version

pytestmark = pytest.mark.valid_at_transition_to("EIP7981")

# Transition forks switch at timestamp 15_000.
PRE_FORK_TIMESTAMP = 14_999
POST_FORK_TIMESTAMP = 15_000


def access_list_shape(addresses: int, keys_per_address: int) -> list:
    """Build an access list with the given shape."""
    return [
        AccessList(
            address=Address(i + 1),
            storage_keys=[Hash(k) for k in range(keys_per_address)],
        )
        for i in range(addresses)
    ]


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
@pytest.mark.parametrize(
    "addresses,keys_per_address",
    [
        pytest.param(1, 0, id="single_address_no_keys"),
        pytest.param(1, 2, id="single_address_two_keys"),
        pytest.param(2, 3, id="two_addresses_three_keys_each"),
    ],
)
def test_access_list_intrinsic_across_amsterdam_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    addresses: int,
    keys_per_address: int,
) -> None:
    """
    Pin the access list intrinsic change across the Amsterdam boundary.

    The same access-list transaction shape is sent in a pre-fork block
    (flat base plus the EIP-2930 per-entry charges, no data cost) and a
    post-fork block (decomposed base, repriced entries, plus the
    EIP-7981 byte surcharge). Each block uses a distinct sender so its
    post-tx balance pins the fork-appropriate intrinsic; the recipient
    is an existing EOA, so no EVM bytecode runs and `gas_used` equals
    the intrinsic exactly.

    The per-fork intrinsic returned by the calculator is also checked
    against a hand-derived per-EIP decomposition, so a calculator
    regression fails here with a clear message rather than only as a
    downstream balance mismatch.
    """
    gas_price = 1_000_000_000
    access_list = access_list_shape(addresses, keys_per_address)
    total_keys = addresses * keys_per_address

    pre_fork = fork.fork_at(timestamp=PRE_FORK_TIMESTAMP)
    post_fork = fork.fork_at(timestamp=POST_FORK_TIMESTAMP)
    pre_costs = pre_fork.gas_costs()
    post_costs = post_fork.gas_costs()

    # Pre-fork: flat base plus the EIP-2930 per-entry charges; access
    # list bytes carry no data cost.
    expected_pre = (
        pre_costs.TX_BASE
        + addresses * pre_costs.TX_ACCESS_LIST_ADDRESS
        + total_keys * pre_costs.TX_ACCESS_LIST_STORAGE_KEY
    )
    # Post-fork: EIP-2780 decomposed base and recipient charge, EIP-8038
    # repriced entry charges, and the EIP-7981 byte surcharge.
    surcharge = (
        calculate_access_list_floor_tokens(access_list)
        * post_costs.TX_DATA_TOKEN_FLOOR
    )
    expected_post = (
        post_costs.TX_BASE
        + post_costs.COLD_ACCOUNT_ACCESS
        + addresses * post_costs.TX_ACCESS_LIST_ADDRESS
        + total_keys * post_costs.TX_ACCESS_LIST_STORAGE_KEY
        + surcharge
    )

    timestamps = [PRE_FORK_TIMESTAMP, POST_FORK_TIMESTAMP]
    expected_intrinsics = [expected_pre, expected_post]
    blocks = []
    post: dict[Address, Account] = {}

    for timestamp, expected_intrinsic in zip(
        timestamps, expected_intrinsics, strict=True
    ):
        sub_fork = fork.fork_at(timestamp=timestamp)
        intrinsic_gas = sub_fork.transaction_intrinsic_cost_calculator()(
            access_list=access_list,
            return_cost_deducted_prior_execution=True,
        )
        assert intrinsic_gas == expected_intrinsic, (
            f"intrinsic at timestamp {timestamp} ({sub_fork}) is "
            f"{intrinsic_gas}, expected {expected_intrinsic}"
        )
        # The intrinsic side must bind so gas_used equals the intrinsic.
        floor_gas = sub_fork.transaction_data_floor_cost_calculator()(
            data=b"", access_list=access_list
        )
        assert floor_gas <= intrinsic_gas

        sender_initial_balance = 10**18
        sender = pre.fund_eoa(sender_initial_balance)
        target = pre.fund_eoa(amount=0)

        tx = Transaction(
            sender=sender,
            to=target,
            gas_limit=intrinsic_gas,
            gas_price=gas_price,
            access_list=access_list,
        )
        blocks.append(Block(timestamp=timestamp, txs=[tx]))

        post[sender] = Account(
            nonce=1,
            balance=sender_initial_balance - intrinsic_gas * gas_price,
        )

    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.inclusion_test
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedBeforeFork()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.RejectedBeforeFork()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedAfterFork()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.RejectedAfterFork()
@pytest.mark.exception_test
def test_access_list_validity_across_amsterdam_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
) -> None:
    """
    Pin the intrinsic-validity flip across the Amsterdam boundary.

    For an access list with one address and two storage keys the
    EIP-7981 byte surcharge (plus the EIP-8038 entry repricing) outgrows
    the EIP-2780 base reduction, so the post-fork intrinsic is strictly
    higher than the pre-fork one. Off-by-one gas limits around each
    fork's requirement then pin all four boundary behaviors:

    1. Pre-fork block with `gas_limit` one below the pre-fork intrinsic
       is rejected.
    2. Pre-fork block accepts both the exact pre-fork intrinsic and a
       gas limit one below the post-fork intrinsic (the new constraint
       is not met, the old one is).
    3. Post-fork block with that same one-below gas limit is rejected.
    4. Post-fork block with the exact post-fork intrinsic is accepted.
    """
    gas_price = 1_000_000_000
    access_list = access_list_shape(addresses=1, keys_per_address=2)

    pre_fork = fork.fork_at(timestamp=PRE_FORK_TIMESTAMP)
    post_fork = fork.fork_at(timestamp=POST_FORK_TIMESTAMP)

    intrinsic_pre = pre_fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list,
        return_cost_deducted_prior_execution=True,
    )
    intrinsic_post = post_fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list,
        return_cost_deducted_prior_execution=True,
    )
    # The gas limit straddling the boundary must be valid pre-fork and
    # invalid post-fork.
    straddle_gas_limit = intrinsic_post - 1
    assert intrinsic_pre <= straddle_gas_limit, (
        f"access list shape does not discriminate: pre-fork intrinsic "
        f"{intrinsic_pre} exceeds post-fork intrinsic - 1 "
        f"({straddle_gas_limit})"
    )
    # The intrinsic side must bind over the floor on both forks.
    for sub_fork, intrinsic in [
        (pre_fork, intrinsic_pre),
        (post_fork, intrinsic_post),
    ]:
        floor_gas = sub_fork.transaction_data_floor_cost_calculator()(
            data=b"", access_list=access_list
        )
        assert floor_gas <= intrinsic

    def make_tx(
        gas_limit: int, error: TransactionException | None = None
    ) -> Transaction:
        return Transaction(
            sender=pre.fund_eoa(),
            to=pre.fund_eoa(amount=0),
            gas_limit=gas_limit,
            gas_price=gas_price,
            access_list=access_list,
            error=error,
        )

    blocks = [
        # 1. Rejected before the fork: below the pre-fork intrinsic.
        Block(
            timestamp=PRE_FORK_TIMESTAMP,
            txs=[
                make_tx(
                    intrinsic_pre - 1,
                    error=TransactionException.INTRINSIC_GAS_TOO_LOW,
                )
            ],
            exception=TransactionException.INTRINSIC_GAS_TOO_LOW,
        ),
        # 2. Accepted before the fork: the exact pre-fork intrinsic and
        # the straddling gas limit that the post-fork rules will reject.
        Block(
            timestamp=PRE_FORK_TIMESTAMP,
            txs=[make_tx(intrinsic_pre), make_tx(straddle_gas_limit)],
        ),
        # 3. Rejected after the fork: the same straddling gas limit.
        Block(
            timestamp=POST_FORK_TIMESTAMP,
            txs=[
                make_tx(
                    straddle_gas_limit,
                    error=TransactionException.INTRINSIC_GAS_TOO_LOW,
                )
            ],
            exception=TransactionException.INTRINSIC_GAS_TOO_LOW,
        ),
        # 4. Accepted after the fork: the exact post-fork intrinsic.
        Block(
            timestamp=POST_FORK_TIMESTAMP,
            txs=[make_tx(intrinsic_post)],
        ),
    ]

    blockchain_test(pre=pre, blocks=blocks, post={})


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_access_list_floor_across_amsterdam_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
) -> None:
    """
    Pin access list bytes entering the calldata floor at the boundary.

    A calldata-heavy access-list transaction binds the floor on both
    sides of the transition: pre-fork the floor counts calldata bytes
    only (access list bytes contribute nothing), post-fork the EIP-7981
    tokens raise it. Each block's gas limit is pinned to its fork's
    floor, so the billed gas equals the floor exactly and an
    implementation that mistimes the floor change fails the receipt and
    balance pins.
    """
    gas_price = 1_000_000_000
    # Sized so the floor dominates the intrinsic on both sides
    # (asserted below): each non-zero byte adds 40 - 16 = 24 gas of
    # floor headroom pre-fork and 64 - 16 = 48 post-fork, outgrowing
    # the per-entry access charges that only the intrinsic carries.
    data = b"\x01" * 400
    access_list = access_list_shape(addresses=1, keys_per_address=2)

    pre_fork = fork.fork_at(timestamp=PRE_FORK_TIMESTAMP)
    post_fork = fork.fork_at(timestamp=POST_FORK_TIMESTAMP)
    pre_costs = pre_fork.gas_costs()
    post_costs = post_fork.gas_costs()

    # Pre-fork (EIP-7623): content-weighted calldata tokens only; the
    # access list bytes contribute nothing to the floor.
    pre_tokens = len(data) * 4
    expected_pre = int(
        pre_costs.TX_BASE + pre_tokens * pre_costs.TX_DATA_TOKEN_FLOOR
    )
    assert pre_fork.transaction_data_floor_cost_calculator()(
        data=data, access_list=access_list
    ) == pre_fork.transaction_data_floor_cost_calculator()(data=data)
    # Post-fork: uniform calldata tokens plus the EIP-7981 access list
    # tokens, anchored on the EIP-2780 decomposed base.
    post_tokens = len(data) * int(
        post_costs.TX_DATA_TOKEN_STANDARD
    ) + calculate_access_list_floor_tokens(access_list)
    expected_post = int(
        post_costs.TX_BASE
        + post_costs.COLD_ACCOUNT_ACCESS
        + post_tokens * post_costs.TX_DATA_TOKEN_FLOOR
    )

    timestamps = [PRE_FORK_TIMESTAMP, POST_FORK_TIMESTAMP]
    expected_floors = [expected_pre, expected_post]
    blocks = []
    post: dict[Address, Account] = {}

    for timestamp, expected_floor in zip(
        timestamps, expected_floors, strict=True
    ):
        sub_fork = fork.fork_at(timestamp=timestamp)
        floor_gas = sub_fork.transaction_data_floor_cost_calculator()(
            data=data, access_list=access_list
        )
        assert floor_gas == expected_floor, (
            f"floor at timestamp {timestamp} ({sub_fork}) is {floor_gas}, "
            f"expected {expected_floor}"
        )
        # The floor must dominate the intrinsic so the transaction is
        # billed exactly the floor.
        intrinsic_gas = sub_fork.transaction_intrinsic_cost_calculator()(
            calldata=data,
            access_list=access_list,
            return_cost_deducted_prior_execution=True,
        )
        assert floor_gas > intrinsic_gas, (
            f"floor {floor_gas} does not dominate intrinsic "
            f"{intrinsic_gas} at timestamp {timestamp} ({sub_fork})"
        )

        sender_initial_balance = 10**18
        sender = pre.fund_eoa(sender_initial_balance)

        tx = Transaction(
            sender=sender,
            to=pre.fund_eoa(amount=0),
            data=data,
            gas_limit=floor_gas,
            gas_price=gas_price,
            access_list=access_list,
            expected_receipt=TransactionReceipt(cumulative_gas_used=floor_gas),
        )
        blocks.append(Block(timestamp=timestamp, txs=[tx]))

        post[sender] = Account(
            nonce=1,
            balance=sender_initial_balance - floor_gas * gas_price,
        )

    blockchain_test(pre=pre, blocks=blocks, post=post)
