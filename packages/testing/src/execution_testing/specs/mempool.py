"""Ethereum mempool admission test spec definition and filler."""

from pprint import pprint
from typing import (
    Callable,
    ClassVar,
    Dict,
    Generator,
    List,
    Mapping,
    Sequence,
    Type,
)

from pydantic import Field

from execution_testing.client_clis import TransitionTool
from execution_testing.exceptions import (
    MempoolException,
    TransactionException,
)
from execution_testing.execution import LabeledExecuteFormat
from execution_testing.fixtures import FixtureFormat, LabeledFixtureFormat
from execution_testing.fixtures.common import FixtureBlobSchedule
from execution_testing.fixtures.mempool import (
    FixtureHead,
    FixtureNextBlock,
    MempoolFixture,
)
from execution_testing.fixtures.state import FixtureConfig
from execution_testing.forks import Fork, TransitionFork
from execution_testing.test_types import Alloc, Environment, Transaction
from execution_testing.test_types.chain_config_types import ChainConfigDefaults

from .base import BaseTest, FillResult
from .debugging import print_traces
from .helpers import verify_transactions

HEAD_BLOCK_TIME = 12
"""Seconds between the head block and the next block."""

CONSENSUS_EXCEPTION_OF: Dict[MempoolException, TransactionException] = {
    MempoolException.NONCE_GAP: TransactionException.NONCE_MISMATCH_TOO_HIGH,
}
"""
Mempool rejections whose transaction is also invalid for the next block,
with the exception the specification raises for it.
"""


class MempoolTest(BaseTest):
    """
    Filler type that tests whether a client admits a single transaction to
    an empty mempool and broadcasts it.
    """

    env: Environment = Field(default_factory=Environment)
    """Environment of the next block, which the head is derived from."""
    pre: Alloc
    tx: Transaction
    broadcast: bool
    exception: (
        List[MempoolException] | TransactionException | MempoolException | None
    ) = None
    """
    Why the pool refuses the transaction. A list names every rule the
    transaction breaks, when a pool may report any of them.
    """
    rules: List[str] = Field(default_factory=list)
    """IDs of the admission rules the test exercises."""
    mempool_rules: Dict[str, str] | None = None
    """Admission rule set versions the expectation assumes."""
    chain_id: int = Field(
        default_factory=lambda: ChainConfigDefaults.chain_id,
        validate_default=True,
    )

    supported_fixture_formats: ClassVar[
        Sequence[FixtureFormat | LabeledFixtureFormat]
    ] = [MempoolFixture]
    supported_execute_formats: ClassVar[Sequence[LabeledExecuteFormat]] = []

    @classmethod
    def genesis_pre_allocation(
        cls,
        *,
        fork: Fork | TransitionFork,
        fixture_format: FixtureFormat | LabeledFixtureFormat,
    ) -> Mapping:
        """Return the accounts the fork allocates at genesis."""
        del fixture_format
        return fork.transitions_from().pre_allocation()

    def consensus_exception(self) -> TransactionException | None:
        """
        Return the exception the specification must raise for the
        transaction in the next block, or `None` if it must accept it.
        """
        if self.exception is None:
            return None
        if isinstance(self.exception, TransactionException):
            return self.exception
        if isinstance(self.exception, list):
            assert not any(
                exception in CONSENSUS_EXCEPTION_OF
                for exception in self.exception
            ), "a list of rejections only names mempool rules"
            return None
        return CONSENSUS_EXCEPTION_OF.get(self.exception)

    def expectation_source(self) -> str:
        """Return where the expected outcome comes from."""
        if self.exception is None or isinstance(
            self.exception, TransactionException
        ):
            return "specification"
        if (
            not isinstance(self.exception, list)
            and self.exception in CONSENSUS_EXCEPTION_OF
        ):
            return "framework"
        return "author"

    def head(self, fork: Fork, env: Environment) -> FixtureHead:
        """
        Return a head whose next block has the values of `env`.

        The head uses exactly its target gas and blob gas, so the base fee
        and the excess blob gas carry over to the next block unchanged.
        """
        assert int(env.number) > 0, "the next block cannot be genesis"
        assert int(env.timestamp) >= HEAD_BLOCK_TIME
        gas_used = int(env.gas_limit) // fork.base_fee_elasticity_multiplier()
        base_fee_per_gas = None
        if env.base_fee_per_gas is not None:
            base_fee_per_gas = int(env.base_fee_per_gas)
            next_base_fee = fork.base_fee_per_gas_calculator()(
                parent_base_fee_per_gas=base_fee_per_gas,
                parent_gas_used=gas_used,
                parent_gas_limit=int(env.gas_limit),
            )
            assert next_base_fee == base_fee_per_gas
        excess_blob_gas = None
        blob_gas_used = None
        if env.excess_blob_gas is not None:
            assert base_fee_per_gas is not None
            excess_blob_gas = int(env.excess_blob_gas)
            blob_gas_used = (
                fork.target_blobs_per_block() * fork.blob_gas_per_blob()
            )
            next_excess_blob_gas = fork.excess_blob_gas_calculator()(
                parent_excess_blob_gas=excess_blob_gas,
                parent_blob_gas_used=blob_gas_used,
                parent_base_fee_per_gas=base_fee_per_gas,
            )
            assert next_excess_blob_gas == excess_blob_gas
        return FixtureHead(
            number=int(env.number) - 1,
            timestamp=int(env.timestamp) - HEAD_BLOCK_TIME,
            gas_limit=env.gas_limit,
            gas_used=gas_used,
            base_fee_per_gas=base_fee_per_gas,
            excess_blob_gas=excess_blob_gas,
            blob_gas_used=blob_gas_used,
        )

    def make_mempool_test_fixture(self, t8n: TransitionTool) -> FillResult:
        """Create a fixture from the mempool test definition."""
        assert self.broadcast == (self.exception is None), (
            "a transaction is broadcast exactly when it has no exception"
        )
        assert self.tx.error is None, (
            "set the expected rejection on the mempool test, not the "
            "transaction"
        )
        fork = self.fork.fork_at(
            block_number=self.env.number, timestamp=self.env.timestamp
        )
        env = self.env.set_fork_requirements(fork)
        env.check_fork_fields(fork)
        tx = self.tx.with_gas_limit(
            max_gas_limit=env.gas_limit,
            transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
            state_gas_reservoir_enabled=fork.state_gas_reservoir_enabled(),
            transaction_total_gas_limit_cap=(
                fork.transaction_total_gas_limit_cap()
            ),
        ).with_signature_and_sender(keep_secret_key=True)
        pre_alloc = self.genesis_alloc(
            self.pre, fork=self.fork, fixture_format=MempoolFixture
        )

        # The specification decides whether the transaction is valid for
        # the next block. An admitted transaction, and one the mempool
        # refuses although it is valid, must both be valid.
        # `Transaction.copy` rebuilds a frame transaction unsigned, so the
        # signed transaction is copied as is.
        checked_tx = tx.model_copy(
            update={"error": self.consensus_exception()}
        )
        transition_tool_output = t8n.evaluate(
            transition_tool_data=TransitionTool.TransitionToolData(
                alloc=pre_alloc,
                txs=[checked_tx],
                env=env,
                fork=fork,
                chain_id=self.chain_id,
                reward=0,
                blob_schedule=fork.blob_schedule(),
                state_test=True,
            ),
        )
        try:
            verify_transactions(
                txs=[checked_tx],
                result=transition_tool_output.result,
                transition_tool_exceptions_reliable=t8n.exception_mapper.reliable,
            )
        except Exception as e:
            print_traces(t8n.get_traces())
            pprint(transition_tool_output.result)
            raise e

        fixture = MempoolFixture(
            network=fork,
            config=FixtureConfig(
                blob_schedule=FixtureBlobSchedule.from_blob_schedule(
                    fork.blob_schedule()
                ),
                chain_id=self.chain_id,
            ),
            head=self.head(fork, env),
            next_block=FixtureNextBlock(
                number=env.number,
                timestamp=env.timestamp,
                base_fee_per_gas=env.base_fee_per_gas,
                excess_blob_gas=env.excess_blob_gas,
            ),
            pre=pre_alloc,
            transaction=tx.rlp(),
            broadcast=self.broadcast,
            exception=self.exception,
            mempool_rules=self.mempool_rules,
            info={
                "mempool": {
                    "expectationSource": self.expectation_source(),
                    "rules": self.rules,
                },
            },
        )
        return FillResult(
            fixture=fixture,
            gas_optimization=None,
            benchmark_gas_used=None,
            benchmark_opcode_count=None,
        )

    def generate(
        self,
        t8n: TransitionTool,
        fixture_format: FixtureFormat | LabeledFixtureFormat,
    ) -> FillResult:
        """Generate the MempoolTest fixture."""
        if fixture_format == MempoolFixture:
            return self.make_mempool_test_fixture(t8n)
        raise Exception(f"Unknown fixture format: {fixture_format}")


MempoolTestSpec = Callable[[str], Generator[MempoolTest, None, None]]
MempoolTestFiller = Type[MempoolTest]
