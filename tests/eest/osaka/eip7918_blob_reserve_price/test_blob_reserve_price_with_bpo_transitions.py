"""Tests EIP-7918 on BPO fork transitions."""

from dataclasses import dataclass
from typing import Iterator, List, Self

import pytest

from ethereum_test_forks import BPO2ToBPO3AtTime15k, Fork
from ethereum_test_tools import (
    EOA,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Hash,
    Header,
    Transaction,
    add_kzg_version,
)
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.utility.pytest import ParameterSet

from .spec import Spec, ref_spec_7918

REFERENCE_SPEC_GIT_PATH = ref_spec_7918.git_path
REFERENCE_SPEC_VERSION = ref_spec_7918.version

BASE_FEE_MAX_CHANGE_DENOMINATOR = 8
ELASTICITY_MULTIPLIER = 2
MIN_BLOB_GASPRICE = 1


@pytest.fixture
def sender(pre: Alloc) -> EOA:
    """Sender account with enough balance for tests."""
    return pre.fund_eoa()


@pytest.fixture
def destination_account(pre: Alloc) -> Address:
    """Contract recipient of blobs."""
    code = Op.STOP
    return pre.deploy_contract(code)


@pytest.fixture
def gas_spender_contract(pre: Alloc) -> Address:
    """Contract that exhausts the gas limit of a tx."""
    code = Op.INVALID
    return pre.deploy_contract(code)


@pytest.fixture
def tx_gas() -> int:
    """Gas limit for blob transactions sent during test."""
    return 21_000


@pytest.fixture
def tx_value() -> int:
    """Value for blob transactions sent during test."""
    return 0


def blob_hashes_per_tx(blobs_per_tx: int) -> List[Hash]:
    """Blob hashes for the transaction."""
    return add_kzg_version(
        [Hash(x) for x in range(blobs_per_tx)],
        Spec.BLOB_COMMITMENT_VERSION_KZG,
    )


@pytest.fixture
def source_fork_target_blobs(fork: Fork) -> int:
    """Transition-from fork target blobs."""
    return fork.target_blobs_per_block(timestamp=0)


@pytest.fixture
def source_fork_gas_per_blob(fork: Fork) -> int:
    """Transition-from fork gas per blob."""
    return fork.blob_gas_per_blob(timestamp=0)


@pytest.fixture
def transition_fork_target_blobs(fork: Fork) -> int:
    """Transition-to fork target blobs."""
    return fork.target_blobs_per_block(timestamp=15_000)


@pytest.fixture
def transition_fork_gas_per_blob(fork: Fork) -> int:
    """Transition-to fork gas per blob."""
    return fork.blob_gas_per_blob(timestamp=15_000)


@pytest.fixture
def env(
    parent_excess_blob_gas: int,
    parent_base_fee_per_gas: int,
    source_fork_target_blobs: int,
    source_fork_gas_per_blob: int,
) -> Environment:
    """Environment for the test."""
    return Environment(
        # Excess blob gas always drops from genesis to block 1 because genesis uses no blob gas.
        excess_blob_gas=parent_excess_blob_gas
        + (source_fork_target_blobs * source_fork_gas_per_blob),
        base_fee_per_gas=(parent_base_fee_per_gas * BASE_FEE_MAX_CHANGE_DENOMINATOR)
        // 7,  # Base fee always drops from genesis to block 1 because the genesis block never
        # tx gas.
        gas_limit=16_000_000,  # To make it easier to reach the requirement with a single tx
    )


def calculate_gas_required_for_base_fee_change(
    *,
    parent_gas_limit: int,
    parent_base_fee_per_gas: int,
    required_base_fee_per_gas: int,
) -> int:
    """
    Calculate the required gas used by transactions to raise or drop the base fee in
    the following block.

    EIP-1559 pseudo code:

    if INITIAL_FORK_BLOCK_NUMBER == block.number:
        expected_base_fee_per_gas = INITIAL_BASE_FEE
    elif parent_gas_used == parent_gas_target:
        expected_base_fee_per_gas = parent_base_fee_per_gas
    elif parent_gas_used > parent_gas_target:
        gas_used_delta = parent_gas_used - parent_gas_target
        base_fee_per_gas_delta = max(
            parent_base_fee_per_gas * gas_used_delta // parent_gas_target \
                // BASE_FEE_MAX_CHANGE_DENOMINATOR,
            1,
        )
        expected_base_fee_per_gas = parent_base_fee_per_gas + base_fee_per_gas_delta
    else:
        gas_used_delta = parent_gas_target - parent_gas_used
        base_fee_per_gas_delta = (
            parent_base_fee_per_gas * gas_used_delta // \
                parent_gas_target // BASE_FEE_MAX_CHANGE_DENOMINATOR
        )
        expected_base_fee_per_gas = parent_base_fee_per_gas - base_fee_per_gas_delta
    """
    parent_gas_target = parent_gas_limit // ELASTICITY_MULTIPLIER

    if parent_base_fee_per_gas == required_base_fee_per_gas:
        parent_gas_used = parent_gas_target
    elif required_base_fee_per_gas > parent_base_fee_per_gas:
        # Base fee needs to go up, so we need to use more than gas_limit // 2
        base_fee_per_gas_delta = required_base_fee_per_gas - parent_base_fee_per_gas
        parent_gas_used = (
            (base_fee_per_gas_delta * BASE_FEE_MAX_CHANGE_DENOMINATOR * parent_gas_target)
            // parent_base_fee_per_gas
        ) + parent_gas_target
    elif required_base_fee_per_gas < parent_base_fee_per_gas:
        # Base fee needs to go down, so we need to use less than gas_limit // 2
        base_fee_per_gas_delta = parent_base_fee_per_gas - required_base_fee_per_gas

        parent_gas_used = (
            parent_gas_target
            - (
                (base_fee_per_gas_delta * BASE_FEE_MAX_CHANGE_DENOMINATOR * parent_gas_target)
                // parent_base_fee_per_gas
            )
            - 1
        )

    if parent_gas_used == parent_gas_target:
        expected_base_fee_per_gas = parent_base_fee_per_gas
    elif parent_gas_used > parent_gas_target:
        gas_used_delta = parent_gas_used - parent_gas_target
        base_fee_per_gas_delta = max(
            parent_base_fee_per_gas
            * gas_used_delta
            // parent_gas_target
            // BASE_FEE_MAX_CHANGE_DENOMINATOR,
            1,
        )
        expected_base_fee_per_gas = parent_base_fee_per_gas + base_fee_per_gas_delta
    else:
        gas_used_delta = parent_gas_target - parent_gas_used
        base_fee_per_gas_delta = (
            parent_base_fee_per_gas
            * gas_used_delta
            // parent_gas_target
            // BASE_FEE_MAX_CHANGE_DENOMINATOR
        )
        expected_base_fee_per_gas = parent_base_fee_per_gas - base_fee_per_gas_delta

    if expected_base_fee_per_gas == required_base_fee_per_gas:
        return parent_gas_used

    raise Exception(
        f"Unable to calculate required gas limit given inputs: gas_limit={parent_gas_limit}, "
        f"parent_base_fee_per_gas={parent_base_fee_per_gas}, "
        f"required_base_fee_per_gas={required_base_fee_per_gas}, "
        f"parent_gas_used={parent_gas_used}, "
        f"expected_base_fee_per_gas={expected_base_fee_per_gas}"
    )


def get_blob_transactions(
    *,
    blob_count: int,
    blob_cap_per_transaction: int | None,
    sender: EOA,
    destination_account: Address,
    tx_gas: int,
    tx_value: int,
    block_base_fee_per_gas: int,
    tx_max_fee_per_blob_gas: int,
) -> List[Transaction]:
    """Return a list of transactions with the given blobs."""
    txs = []
    if blob_cap_per_transaction is None:
        blob_cap_per_transaction = blob_count
    for _ in range(blob_count // blob_cap_per_transaction):
        tx = Transaction(
            ty=Spec.BLOB_TX_TYPE,
            sender=sender,
            to=destination_account,
            value=tx_value,
            gas_limit=tx_gas,
            max_fee_per_gas=block_base_fee_per_gas,
            max_priority_fee_per_gas=0,
            max_fee_per_blob_gas=tx_max_fee_per_blob_gas,
            access_list=[],
            blob_versioned_hashes=blob_hashes_per_tx(blob_cap_per_transaction),
        )
        txs.append(tx)
    if blob_count % blob_cap_per_transaction != 0:
        tx = Transaction(
            ty=Spec.BLOB_TX_TYPE,
            sender=sender,
            to=destination_account,
            value=tx_value,
            gas_limit=tx_gas,
            max_fee_per_gas=block_base_fee_per_gas,
            max_priority_fee_per_gas=0,
            max_fee_per_blob_gas=tx_max_fee_per_blob_gas,
            access_list=[],
            blob_versioned_hashes=blob_hashes_per_tx(blob_count % blob_cap_per_transaction),
        )
        txs.append(tx)
    return txs


@pytest.fixture
def tx_max_fee_per_blob_gas() -> int:
    """Max fee per blob gas to be used by all transactions in the test."""
    return 0x1000


@pytest.fixture
def blob_cap_per_transaction(fork: Fork) -> int:
    """Max blobs that a single transaction can contain."""
    return fork.max_blobs_per_tx()


@pytest.fixture
def parent_block_txs(
    sender: EOA,
    destination_account: Address,
    gas_spender_contract: Address,
    env: Environment,
    tx_gas: int,
    tx_value: int,
    parent_blob_count: int,
    parent_base_fee_per_gas: int,
    tx_max_fee_per_blob_gas: int,
    transition_block_base_fee_per_gas: int,
    blob_cap_per_transaction: int,
) -> List[Transaction]:
    """
    Transactions included in the block prior to the fork transition fork.

    Includes blob transactions to raise the `parent_blob_gas_used` and normal transactions
    to raise/lower the base fee per gas.
    """
    parent_block_blob_txs = get_blob_transactions(
        blob_count=parent_blob_count,
        blob_cap_per_transaction=blob_cap_per_transaction,
        sender=sender,
        destination_account=destination_account,
        tx_gas=tx_gas,
        tx_value=tx_value,
        block_base_fee_per_gas=parent_base_fee_per_gas * 10,
        tx_max_fee_per_blob_gas=tx_max_fee_per_blob_gas,
    )
    required_gas_used = calculate_gas_required_for_base_fee_change(
        parent_gas_limit=env.gas_limit,
        parent_base_fee_per_gas=parent_base_fee_per_gas,
        required_base_fee_per_gas=transition_block_base_fee_per_gas,
    )
    blob_txs_execution_gas = sum(tx.gas_limit for tx in parent_block_blob_txs)
    assert blob_txs_execution_gas <= required_gas_used
    extra_tx_gas_limit = required_gas_used - blob_txs_execution_gas
    assert extra_tx_gas_limit >= 21_000

    extra_tx = Transaction(
        sender=sender,
        to=gas_spender_contract,
        gas_limit=extra_tx_gas_limit,
        max_fee_per_gas=parent_base_fee_per_gas,
        max_priority_fee_per_gas=0,
        access_list=[],
    )
    return parent_block_blob_txs + [extra_tx]


@pytest.fixture
def parent_block(
    parent_block_txs: List[Transaction],
    parent_excess_blob_gas: int,
    parent_blob_count: int,
    parent_base_fee_per_gas: int,
    blob_gas_per_blob: int,
) -> Block:
    """Parent block to satisfy the pre-fork conditions of the test."""
    return Block(
        txs=parent_block_txs,
        timestamp=14_999,
        header_verify=Header(
            excess_blob_gas=parent_excess_blob_gas,
            blob_gas_used=parent_blob_count * blob_gas_per_blob,
            base_fee_per_gas=parent_base_fee_per_gas,
        ),
    )


@pytest.fixture
def transition_block_txs(
    sender: EOA,
    destination_account: Address,
    tx_gas: int,
    tx_value: int,
    transition_block_blob_count: int,
    blob_cap_per_transaction: int,
    tx_max_fee_per_blob_gas: int,
    transition_block_base_fee_per_gas: int,
) -> List[Transaction]:
    """
    Transactions included in the first block of the new fork.

    Includes blob transactions only.
    """
    return get_blob_transactions(
        blob_count=transition_block_blob_count,
        blob_cap_per_transaction=blob_cap_per_transaction,
        sender=sender,
        destination_account=destination_account,
        tx_gas=tx_gas,
        tx_value=tx_value,
        block_base_fee_per_gas=transition_block_base_fee_per_gas * 10,
        tx_max_fee_per_blob_gas=tx_max_fee_per_blob_gas,
    )


@pytest.fixture
def transition_block(
    transition_block_txs: List[Transaction],
    transition_block_expected_excess_blob_gas: int | None,
    transition_block_blob_count: int,
    transition_block_base_fee_per_gas: int,
    blob_gas_per_blob: int,
) -> Block:
    """Parent block to satisfy the pre-fork conditions of the test."""
    return Block(
        txs=transition_block_txs,
        timestamp=15_000,
        header_verify=Header(
            excess_blob_gas=transition_block_expected_excess_blob_gas,
            blob_gas_used=transition_block_blob_count * blob_gas_per_blob,
            base_fee_per_gas=transition_block_base_fee_per_gas,
        ),
    )


@dataclass(kw_only=True)
class ParentHeader:
    """Parent block header information."""

    excess_blob_gas: int
    blob_gas_used: int
    base_fee_per_gas: int


@dataclass(kw_only=True)
class BlobSchedule:
    """Blob schedule for a fork."""

    max: int
    target: int
    base_fee_update_fraction: int
    blob_gas_per_blob: int
    blob_base_cost: int | None

    @classmethod
    def from_fork(cls, fork: Fork, timestamp: int) -> Self:
        """Return an instance of the blob schedule given the fork."""
        blob_base_cost = None
        if fork.blob_reserve_price_active(timestamp=timestamp):
            blob_base_cost = fork.blob_base_cost(timestamp=timestamp)
        return cls(
            max=fork.max_blobs_per_block(timestamp=timestamp),
            target=fork.target_blobs_per_block(timestamp=timestamp),
            base_fee_update_fraction=fork.blob_base_fee_update_fraction(timestamp=timestamp),
            blob_gas_per_blob=fork.blob_gas_per_blob(timestamp=timestamp),
            blob_base_cost=blob_base_cost,
        )

    @property
    def target_blob_gas_per_block(self) -> int:
        """Return the target blob gas per block."""
        return self.target * self.blob_gas_per_blob

    @staticmethod
    def taylor_exponential(factor: int, numerator: int, denominator: int) -> int:
        """
        Approximates factor * e ** (numerator / denominator) using Taylor expansion.

        This function is used to compute the blob gas price.
        """
        i = 1
        output = 0
        numerator_accum = factor * denominator
        while numerator_accum > 0:
            output += numerator_accum
            numerator_accum = (numerator_accum * numerator) // (denominator * i)
            i += 1
        return output // denominator

    def calculate_blob_gas_price(self, excess_blob_gas: int) -> int:
        """
        Calculate the blob gasprice for a block.

        Parameters
        ----------
        excess_blob_gas :
            The excess blob gas for the block.

        Returns
        -------
        blob_gasprice: `Uint`
            The blob gasprice.

        """
        return BlobSchedule.taylor_exponential(
            MIN_BLOB_GASPRICE,
            excess_blob_gas,
            self.base_fee_update_fraction,
        )

    def calculate_excess_blob_gas(self, parent_header: ParentHeader) -> int:
        """
        Calculate the excess blob gas for the current block based
        on the gas used in the parent block.
        """
        parent_blob_gas = parent_header.excess_blob_gas + parent_header.blob_gas_used
        if parent_blob_gas < self.target_blob_gas_per_block:
            return 0

        target_blob_gas_price = self.blob_gas_per_blob
        target_blob_gas_price *= self.calculate_blob_gas_price(parent_header.excess_blob_gas)

        if self.blob_base_cost is not None:
            base_blob_tx_price = self.blob_base_cost * parent_header.base_fee_per_gas
            if base_blob_tx_price > target_blob_gas_price:
                blob_schedule_delta = self.max - self.target
                return (
                    parent_header.excess_blob_gas
                    + parent_header.blob_gas_used * blob_schedule_delta // self.max
                )

        return parent_blob_gas - self.target_blob_gas_per_block

    def execution_base_fee_threshold_from_excess_blob_gas(
        self, excess_blob_gas: int
    ) -> int | None:
        """
        Return the minimum base fee required to trigger the reserve mechanism, or None
        for blob schedules that don't have a reserve price mechanism.
        """
        if self.blob_base_cost is None:
            return None
        target_blob_gas_price = self.blob_gas_per_blob
        target_blob_gas_price *= self.calculate_blob_gas_price(excess_blob_gas)
        base_blob_tx_price = target_blob_gas_price
        return (base_blob_tx_price // self.blob_base_cost) + 1


def get_fork_scenarios(fork: Fork) -> Iterator[ParameterSet]:
    """
    Return the list of scenarios at the fork boundary depending on the source fork and
    transition fork properties.
    """
    source_blob_schedule = BlobSchedule.from_fork(fork=fork, timestamp=0)
    transition_blob_schedule = BlobSchedule.from_fork(fork=fork, timestamp=15_000)

    excess_blobs_combinations = [0, 1, 10, 100]

    for parent_excess_blobs in excess_blobs_combinations:
        parent_excess_blob_gas = parent_excess_blobs * source_blob_schedule.blob_gas_per_blob

        source_execution_threshold = (
            source_blob_schedule.execution_base_fee_threshold_from_excess_blob_gas(
                parent_excess_blob_gas
            )
        )
        transition_execution_threshold = (
            transition_blob_schedule.execution_base_fee_threshold_from_excess_blob_gas(
                parent_excess_blob_gas
            )
        )
        if (
            source_execution_threshold != transition_execution_threshold
            and transition_execution_threshold is not None
        ):
            # The source base fee reserve threshold is different from the transition one
            # given the excess blob gas.
            # We can verify that the BPO is activated correctly by using the a setup block
            # with transition_execution_threshold to trigger the reserve.
            for source_blob_count in [0, source_blob_schedule.target, source_blob_schedule.max]:
                # Scenario 1: Parent base fee per gas is below the threshold at the
                # parent of the transition block, so even though the base fee increases on
                # the transition block to reach the value required to activate the reserve,
                # since the base fee per gas of the parent is used, the reserve must not be
                # activated.
                parent_base_fee = transition_execution_threshold - 1
                transition_base_fee = transition_execution_threshold
                parent_header = ParentHeader(
                    excess_blob_gas=parent_excess_blob_gas,
                    blob_gas_used=source_blob_count,
                    base_fee_per_gas=parent_base_fee,
                )
                target_excess_blob_gas = transition_blob_schedule.calculate_excess_blob_gas(
                    parent_header
                )
                source_excess_blob_gas = source_blob_schedule.calculate_excess_blob_gas(
                    parent_header
                )
                if source_excess_blob_gas != target_excess_blob_gas:
                    yield pytest.param(
                        parent_base_fee,
                        parent_excess_blob_gas,
                        source_blob_count,
                        transition_base_fee,
                        transition_blob_schedule.target,
                        None,
                        id=(
                            "below_reserve_base_fee_threshold-"
                            f"parent_excess_blobs_{parent_excess_blobs}-"
                            f"parent_blobs_{source_blob_count}"
                        ),
                    )

                # Scenario 2: Parent base fee per gas is at the threshold, so the reserve
                # is activated even though the base fee per gas decreases below the
                # threshold on the transition block.
                parent_base_fee = transition_execution_threshold
                transition_base_fee = transition_execution_threshold - 1
                parent_header = ParentHeader(
                    excess_blob_gas=parent_excess_blob_gas,
                    blob_gas_used=source_blob_count,
                    base_fee_per_gas=parent_base_fee,
                )
                target_excess_blob_gas = transition_blob_schedule.calculate_excess_blob_gas(
                    parent_header
                )
                source_excess_blob_gas = source_blob_schedule.calculate_excess_blob_gas(
                    parent_header
                )
                if source_excess_blob_gas != target_excess_blob_gas:
                    yield pytest.param(
                        parent_base_fee,
                        parent_excess_blob_gas,
                        source_blob_count,
                        transition_base_fee,
                        transition_blob_schedule.target,
                        None,
                        id=(
                            "at_reserve_base_fee_threshold-"
                            f"parent_excess_blobs_{parent_excess_blobs}-"
                            f"parent_blobs_{source_blob_count}"
                        ),
                    )

    if fork == BPO2ToBPO3AtTime15k:
        # Explicitly add the exact scenario that triggered the Fusaka Devnet-4 fork.
        yield pytest.param(
            0x32,
            0x125BF5F,
            19,
            0x33,
            9,
            0x132CF5F,
            id="devnet-4-fork-scenario",
        )


@pytest.mark.parametrize_by_fork(
    [
        "parent_base_fee_per_gas",
        "parent_excess_blob_gas",
        "parent_blob_count",
        "transition_block_base_fee_per_gas",
        "transition_block_blob_count",
        "transition_block_expected_excess_blob_gas",
    ],
    get_fork_scenarios,
)
@pytest.mark.valid_at_transition_to("Osaka", subsequent_forks=True)
@pytest.mark.valid_for_bpo_forks()
def test_reserve_price_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    parent_block: Block,
    transition_block: Block,
    env: Environment,
):
    """Test reserve price mechanism across various block base fee and excess blob gas scenarios."""
    blockchain_test(
        pre=pre,
        post={},
        blocks=[parent_block, transition_block],
        genesis_environment=env,
    )
