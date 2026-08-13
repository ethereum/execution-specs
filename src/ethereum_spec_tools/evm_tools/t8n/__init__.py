"""
Create a transition tool for the given fork.

The ``T8N`` class consumes testing-package pydantic types directly; the
JSON CLI surface lives in :mod:`.cli`.
"""

from contextlib import AbstractContextManager
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Final,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
)

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U64, U256, Uint
from typing_extensions import override

from ethereum import trace
from ethereum.exceptions import EthereumException, InvalidBlock
from ethereum.fork_criteria import ByBlockNumber, ByTimestamp, Unscheduled
from ethereum_spec_tools.forks import (
    ForkOverrides,
    Hardfork,
    TemporaryHardfork,
)

from ..loaders.fixture_loader import Load
from ..loaders.transaction_loader import TransactionLoad, UnsupportedTxError
from ..utils import get_stream_logger, resolve_fork
from .block_environment import Ommer, build_block_environment
from .evm_trace.group import GroupTracer
from .result import build_result, record_rejected_tx

if TYPE_CHECKING:
    from execution_testing.client_clis.cli_types import (
        TransitionToolOutput,
    )
    from execution_testing.client_clis.transition_tool import (
        TransitionTool,
    )
    from execution_testing.exceptions import ExceptionMapper
    from execution_testing.test_types import (
        Environment as TestingEnvironment,
    )
    from execution_testing.test_types import (
        Transaction as TestingTransaction,
    )

    TransitionToolData = TransitionTool.TransitionToolData

T = TypeVar("T")


class ForkCache(AbstractContextManager):
    """
    Stores references to temporary hardforks and cleans them up when exited.
    """

    _cache: Final[dict[tuple[str, ForkOverrides], TemporaryHardfork]]

    def __init__(self) -> None:
        self._cache = {}

    @override
    def __exit__(self, *args: object, **kwargs: object) -> None:
        for fork in self._cache.values():
            fork.__exit__(*args, **kwargs)
        self._cache.clear()

    def get(
        self,
        template: Hardfork,
        fork_criteria: ByBlockNumber | ByTimestamp | Unscheduled | None = None,
        blob_target_gas_per_block: U64 | None = None,
        gas_per_blob: U64 | None = None,
        blob_min_gasprice: Uint | None = None,
        blob_base_fee_update_fraction: Uint | None = None,
        max_blob_gas_per_block: U64 | None = None,
        blob_schedule_target: U64 | None = None,
        blob_schedule_max: U64 | None = None,
    ) -> Hardfork:
        """
        Search the cache for a matching hardfork, or create one if it doesn't
        exist.
        """
        overrides = ForkOverrides(
            fork_criteria=fork_criteria,
            blob_target_gas_per_block=blob_target_gas_per_block,
            gas_per_blob=gas_per_blob,
            blob_min_gasprice=blob_min_gasprice,
            blob_base_fee_update_fraction=blob_base_fee_update_fraction,
            max_blob_gas_per_block=max_blob_gas_per_block,
            blob_schedule_target=blob_schedule_target,
            blob_schedule_max=blob_schedule_max,
        )
        if overrides.matches_template(template):
            return template

        cache_key = (template.short_name, overrides)
        try:
            return self._cache[cache_key]
        except KeyError:
            pass

        clone = Hardfork.clone(template=template, overrides=overrides)
        self._cache[cache_key] = clone
        return clone


class T8N(Load):
    """
    Execute the transition function on already-parsed inputs.

    ``T8N`` is JSON-free: callers hand in a testing
    ``TransitionTool.TransitionToolData`` (alloc / env / txs /
    blob_schedule / fork / chain_id / reward / state_test) plus any
    pre-PoS ommer data, and ``run()`` returns a
    :class:`~execution_testing.client_clis.cli_types.TransitionToolOutput`.
    See :mod:`.cli` for the JSON wrapper used by the
    ``ethereum-spec-evm t8n`` entry point.
    """

    tracers: Final[GroupTracer | None]
    alloc: Any
    env: "TestingEnvironment"
    txs: List["TestingTransaction"]
    ommers: List[Ommer]
    rejected_transactions: List[Any]
    body: Bytes
    state_test: bool
    state_reward: int
    exception_mapper: Optional["ExceptionMapper"]
    inclusion_list_txs: Optional[List["TestingTransaction"]]
    _block_exception: Optional[str]

    def __init__(
        self,
        t8n_data: "TransitionToolData",
        *,
        cache: ForkCache,
        fork_block: Optional[int] = None,
        ommers: Sequence[Ommer] = (),
        tracers: Optional[GroupTracer] = None,
        exception_mapper: Optional["ExceptionMapper"] = None,
    ) -> None:
        # ``resolve_fork`` only maps the testing fork name to a spec
        # ``Hardfork`` module — CLI exception aliases like
        # ``HomesteadToDaoAt5`` are unfolded by ``find_fork`` in
        # :mod:`.cli` before the testing ``Fork`` is constructed. For
        # those transition-fork tests the CLI also reports the block
        # number at which the resolved fork activates via
        # ``fork_block``; the in-process path leaves it ``None``.
        fork_module = resolve_fork(t8n_data.fork_name)
        fork_criteria: Optional[ByBlockNumber] = None
        if fork_block is not None and fork_block != 0:
            fork_criteria = ByBlockNumber(fork_block)

        # Translate ``t8n_data.blob_params`` (testing ``ForkBlobSchedule``)
        # into the override arguments ``ForkCache.get`` consumes.
        #
        # Only forward overrides for BPO forks. BPO forks share their
        # non-BPO ancestor's spec module and rely on the override to
        # differentiate their blob schedule. Non-BPO forks (Cancun,
        # Prague, Amsterdam, …) carry the correct schedule built into
        # their spec module — overriding here would force ``ForkCache``
        # to clone the fork into a temporary directory whenever the
        # override values don't byte-match the constants, attributing
        # all opcode coverage to the clone's ``/tmp/...`` paths instead
        # of the original ``src/ethereum/forks/<fork>/`` source.
        target_blobs_per_block: Optional[U64] = None
        max_blobs_per_block: Optional[U64] = None
        base_fee_update_fraction: Optional[Uint] = None
        if (
            t8n_data.blob_params is not None
            and t8n_data.fork.bpo_fork()
            and t8n_data.fork != t8n_data.fork.non_bpo_ancestor()
        ):
            target_blobs_per_block = U64(
                int(t8n_data.blob_params.target_blobs_per_block)
            )
            max_blobs_per_block = U64(
                int(t8n_data.blob_params.max_blobs_per_block)
            )
            base_fee_update_fraction = Uint(
                int(t8n_data.blob_params.base_fee_update_fraction)
            )

        fork = cache.get(
            fork_module,
            fork_criteria,
            blob_schedule_target=target_blobs_per_block,
            blob_schedule_max=max_blobs_per_block,
            blob_base_fee_update_fraction=base_fee_update_fraction,
        )

        if tracers is not None:
            trace.set_evm_trace(tracers)
        self.tracers = tracers

        self.logger = get_stream_logger("T8N")
        super().__init__(fork)

        self.chain_id = U64(t8n_data.chain_id)
        self.state_test = t8n_data.state_test
        self.state_reward = t8n_data.reward
        self.exception_mapper = exception_mapper

        from execution_testing.client_clis.cli_types import LazyAlloc

        # Take a defensive copy of the input alloc so ``apply_diff``
        # (and any other in-place mutation T8N does) never escapes
        # into the caller's Python object. Without this, multi-block
        # tests that contain an invalid block would observe a mutated
        # pre-state — the testing framework expects ``previous_alloc``
        # to remain unchanged when ``block.exception`` is set.
        input_alloc = t8n_data.alloc
        if isinstance(input_alloc, LazyAlloc):
            input_alloc = input_alloc.materialize()
        self.alloc = input_alloc.model_copy(deep=True)
        self.env = t8n_data.env
        self.txs = list(t8n_data.txs)
        self.ommers = list(ommers)
        self.body = Bytes(rlp.encode([tx.rlp() for tx in self.txs]))
        self.rejected_transactions = []
        self.inclusion_list_txs = (
            list(t8n_data.inclusion_list_txs)
            if t8n_data.inclusion_list_txs is not None
            else None
        )

    def _tracer(self, type_: Type[T]) -> T:
        group = self.tracers
        if group is None:
            raise Exception("no tracer configured")
        found = next((x for x in group.tracers if isinstance(x, type_)), None)
        if found is None:
            raise Exception(f"no tracer of type `{type_}` found")
        return found

    def block_environment(self) -> Any:
        """
        Build the fork's ``BlockEnvironment`` for the current block.

        Side effect: stores the resulting ``BlockState`` on ``self`` so
        ``extract_block_diff`` can be called after execution.
        """
        block_env = build_block_environment(
            fork=self.fork,
            env=self.env,
            pre_state=self.alloc,
            chain_id=self.chain_id,
            state_test=self.state_test,
        )
        self._block_state = block_env.state
        return block_env

    def convert_transaction(self, tx: "TestingTransaction") -> Any:
        """
        Convert a testing ``Transaction`` into the fork's tx object.

        TODO: Replace with ``self.fork.decode_transaction(tx.rlp())``
        once two pieces land in a follow-up PR:

        1. Pre-Berlin forks gain a ``decode_transaction``. Pre-Berlin forks
           predate typed txs and currently expose no decode entry
           point — block decoding produces the legacy class directly.
        2. The testing exception_mapper learns to surface
           ``DecodingError`` (raised when a contract-creating typed tx
           like ``BlobTransaction`` (``to=None``) reaches
           ``decode_transaction``) as the canonical
           ``TransactionTypeContractCreationError``. Today
           ``TransactionLoad`` constructs the tx object even when its
           shape is illegal for the fork, so ``check_transaction``
           inside ``process_transaction`` raises the canonical error.

        Until both are in place, we go through ``TransactionLoad``
        (the JSON loader) which handles both concerns.
        """
        raw: Dict[str, Any] = tx.model_dump(
            mode="json", by_alias=True, exclude_none=True
        )
        # Bridge testing-side aliases (geth-compatible) to the names
        # ``TransactionLoad`` expects.
        if "input" in raw:
            raw.setdefault("data", raw["input"])
        if "gas" in raw:
            raw.setdefault("gasLimit", raw["gas"])
        # ``to == None`` is dumped as JSON ``null``; ``TransactionLoad``
        # treats the empty string as the contract-creation sentinel.
        if raw.get("to") in (None, "0x"):
            raw["to"] = ""
        # Ensure the ``type`` field is set so ``TransactionLoad``
        # dispatches to the right tx class (testing's dump uses ``ty``
        # which serializes to ``type`` only on some fork variants).
        raw.setdefault("type", "0x" + format(int(tx.ty), "02x"))
        return TransactionLoad(raw, self.fork).read()

    def pay_block_rewards(self, block_reward: U256, block_env: Any) -> None:
        """Apply the block rewards to the block coinbase."""
        ommer_count = U256(len(self.ommers))
        miner_reward = block_reward + (
            ommer_count * (block_reward // U256(32))
        )

        rewards_state = self.fork.TransactionState(parent=block_env.state)

        self.fork.create_ether(rewards_state, block_env.coinbase, miner_reward)

        for ommer in self.ommers:
            # ``delta`` is the age of the ommer relative to the current block.
            ommer_age = U256(int(ommer.delta, 16))
            ommer_miner_reward = (
                (U256(8) - ommer_age) * block_reward
            ) // U256(8)
            self.fork.create_ether(
                rewards_state, ommer.address, ommer_miner_reward
            )

        self.fork.incorporate_tx_into_block(rewards_state)

    def _process_txs(self, block_env: Any, block_output: Any) -> None:
        """Execute every transaction in ``self.txs`` against ``block_env``."""
        for tx_index, testing_tx in enumerate(self.txs):
            try:
                fork_tx = self.convert_transaction(testing_tx)
                self.fork.process_transaction(
                    block_env, block_output, fork_tx, Uint(tx_index)
                )
            except (EthereumException, UnsupportedTxError) as e:
                # `UnsupportedTxError` covers ``convert_transaction``
                # failures when a typed tx is structurally malformed for
                # this fork (e.g. a contract-creating BlobTransaction).
                record_rejected_tx(self, tx_index, e)
                self.logger.warning(f"Transaction {tx_index} failed: {e!r}")

    def run_state_test(self) -> None:
        """
        Apply a single transaction on pre-state. No system operations
        are performed.
        """
        self._block_env = self.block_environment()
        self._block_output = self.fork.BlockOutput()

        if len(self.txs) > 0:
            testing_tx = self.txs[0]
            try:
                fork_tx = self.convert_transaction(testing_tx)
                self.fork.process_transaction(
                    block_env=self._block_env,
                    block_output=self._block_output,
                    tx=fork_tx,
                    index=Uint(0),
                )
            except (EthereumException, UnsupportedTxError) as e:
                record_rejected_tx(self, 0, e)
                self.logger.warning(f"Transaction 0 failed: {e!r}")

        self._block_exception = None
        self.result = build_result(
            self,
            self._block_env,
            self._block_output,
            self._block_exception,
            self.rejected_transactions,
        )

    def _run_blockchain_test(self, block_env: Any, block_output: Any) -> None:
        if self.fork.has_compute_requests_hash:
            self.fork.process_unchecked_system_transaction(
                block_env=block_env,
                target_address=self.fork.HISTORY_STORAGE_ADDRESS,
                data=block_env.block_hashes[-1],  # The parent hash
            )

        if self.fork.has_beacon_roots_address:
            self.fork.process_unchecked_system_transaction(
                block_env=block_env,
                target_address=self.fork.BEACON_ROOTS_ADDRESS,
                data=block_env.parent_beacon_block_root,
            )

        self._process_txs(block_env, block_output)

        # EIP-7928: Post-execution operations use index N+1
        if self.fork.has_hash_block_access_list:
            block_env.block_access_list_builder.block_access_index = (
                self.fork.BlockAccessIndex(Uint(len(self.txs)) + Uint(1))
            )

        if not self.fork.proof_of_stake and self.state_reward != -1:
            # ``-1`` is the sentinel for "skip block rewards entirely"
            # (testing-side ``TransitionToolData.__post_init__`` sets
            # this for genesis blocks; the CLI wrapper resolves a
            # ``--state.reward=None`` to the fork's ``BLOCK_REWARD``
            # before constructing the data).
            self.pay_block_rewards(U256(self.state_reward), block_env)

        if self.fork.has_inclusion_list_satisfied:
            block_output.inclusion_list_satisfied = (
                (
                    self.fork.check_inclusion_list_transactions(
                        block_env,
                        block_output,
                        tuple(
                            self.fork.encode_transaction(
                                self.convert_transaction(tx)
                            )
                            for tx in self.txs
                        ),
                        tuple(
                            self.fork.encode_transaction(
                                self.convert_transaction(tx)
                            )
                            for tx in self.inclusion_list_txs
                        ),
                    )
                )
                if self.inclusion_list_txs is not None
                else True
            )

        if self.fork.has_withdrawal:
            withdrawals = self.env.withdrawals or []
            fork_withdrawals = tuple(
                self.fork.Withdrawal(
                    Uint(int(w.index)),
                    Uint(int(w.validator_index)),
                    self.fork.hex_to_address(w.address.hex()),
                    U256(int(w.amount)),
                )
                for w in withdrawals
            )
            self.fork.process_withdrawals(
                block_env, block_output, fork_withdrawals
            )

        if self.fork.has_compute_requests_hash:
            self.fork.process_general_purpose_requests(block_env, block_output)

        if self.fork.has_hash_block_access_list:
            block_output.block_access_list = self.fork.build_block_access_list(
                block_env.block_access_list_builder, block_env.state
            )

            # Validate block access list gas limit constraint (EIP-7928)
            self.fork.validate_block_access_list_gas_limit(
                block_access_list=block_output.block_access_list,
                block_gas_limit=block_env.block_gas_limit,
            )

    def run_blockchain_test(self) -> None:
        """
        Apply a block on the pre-state. Also includes system operations.
        """
        self._block_env = self.block_environment()
        self._block_output = self.fork.BlockOutput()
        self._block_exception = None

        try:
            self._run_blockchain_test(self._block_env, self._block_output)
        except InvalidBlock as e:
            self._block_exception = f"{e}"

        self.result = build_result(
            self,
            self._block_env,
            self._block_output,
            self._block_exception,
            self.rejected_transactions,
        )

    def run(self) -> "TransitionToolOutput":
        """
        Execute the transition; return the in-memory result.

        The returned ``TransitionToolOutput`` carries the post-state
        ``Alloc`` as a ``MaterializedAlloc`` (already in memory, so
        ``get()`` is a no-op), the ``Result`` (state root, receipts,
        rejected txs, block exception, …), and the encoded transaction
        body as raw RLP bytes. The JSON CLI surface lives in
        :func:`.cli.write_t8n_outputs`.
        """
        from execution_testing.base_types import Bytes as TestingBytes
        from execution_testing.client_clis.cli_types import (
            MaterializedAlloc,
            TransitionToolOutput,
        )

        if self.state_test:
            self.run_state_test()
        else:
            self.run_blockchain_test()

        # Apply the block diff in place so ``self.alloc`` is the
        # post-state when the caller reads it. Safe to do
        # unconditionally — ``self.alloc`` is a defensive copy taken
        # in ``__init__``, so mutating it never escapes to the caller.
        diff = self.fork.extract_block_diff(self._block_state)
        self.alloc.apply_diff(diff)

        return TransitionToolOutput(
            alloc=MaterializedAlloc(
                alloc=self.alloc,
                _state_root=self.result.state_root,
            ),
            result=self.result,
            body=TestingBytes(self.body),
        )
