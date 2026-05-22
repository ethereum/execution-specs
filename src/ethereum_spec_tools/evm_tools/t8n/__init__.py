"""
Create a transition tool for the given fork.
"""

import argparse
import fnmatch
import json
import os
from contextlib import AbstractContextManager
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Final,
    List,
    Optional,
    TextIO,
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
from ..utils import (
    FatalError,
    find_fork,
    get_stream_logger,
    parse_hex_or_int,
)
from .env import Ommer, build_block_environment
from .evm_trace.count import CountTracer
from .evm_trace.eip3155 import Eip3155Tracer
from .evm_trace.group import GroupTracer
from .result import build_result, record_rejected_tx

if TYPE_CHECKING:
    from execution_testing.exceptions import ExceptionMapper
    from execution_testing.test_types import (
        Alloc as TestingAlloc,
    )
    from execution_testing.test_types import (
        Environment as TestingEnvironment,
    )
    from execution_testing.test_types import (
        Transaction as TestingTransaction,
    )

T = TypeVar("T")


def t8n_arguments(subparsers: argparse._SubParsersAction) -> None:
    """
    Adds the arguments for the t8n tool subparser.
    """
    t8n_parser = subparsers.add_parser("t8n", help="This is the t8n tool.")

    t8n_parser.add_argument(
        "--input.alloc", dest="input_alloc", type=str, default="alloc.json"
    )
    t8n_parser.add_argument(
        "--input.env", dest="input_env", type=str, default="env.json"
    )
    t8n_parser.add_argument(
        "--input.txs", dest="input_txs", type=str, default="txs.json"
    )
    t8n_parser.add_argument(
        "--input.blobParams",
        dest="blob_parameters",
        type=str,
        default=None,
    )
    t8n_parser.add_argument(
        "--output.alloc", dest="output_alloc", type=str, default="alloc.json"
    )
    t8n_parser.add_argument(
        "--output.basedir", dest="output_basedir", type=str, default="."
    )
    t8n_parser.add_argument("--output.body", dest="output_body", type=str)
    t8n_parser.add_argument(
        "--output.result",
        dest="output_result",
        type=str,
        default="result.json",
    )
    t8n_parser.add_argument(
        "--state.chainid", dest="state_chainid", type=int, default=1
    )
    t8n_parser.add_argument(
        "--state.fork", dest="state_fork", type=str, default="Frontier"
    )
    t8n_parser.add_argument(
        "--state.reward", dest="state_reward", type=int, default=None
    )
    t8n_parser.add_argument("--trace", action="store_true")
    t8n_parser.add_argument("--trace.memory", action="store_true")
    t8n_parser.add_argument("--trace.nomemory", action="store_true")
    t8n_parser.add_argument("--trace.noreturndata", action="store_true")
    t8n_parser.add_argument("--trace.nostack", action="store_true")
    t8n_parser.add_argument("--trace.returndata", action="store_true")

    t8n_parser.add_argument("--opcode.count", dest="opcode_count", type=str)

    t8n_parser.add_argument("--state-test", action="store_true")


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


def _read_json_input(
    path_or_stdin: str, stdin: Optional[Dict], key: str
) -> Any:
    """Read one of the t8n JSON inputs (alloc/env/txs) per the CLI flags."""
    if path_or_stdin == "stdin":
        assert stdin is not None
        return stdin[key]
    with open(path_or_stdin, "r") as f:
        return json.load(f)


def _parse_ommers_from_env_json(env_json: Any, fork: Any) -> List[Ommer]:
    """Parse the pre-PoS ``ommers`` block from a raw env JSON dict."""
    ommers: List[Ommer] = []
    for raw in env_json.get("ommers", []):
        ommers.append(
            Ommer(
                delta=raw["delta"],
                address=fork.hex_to_address(raw["address"]),
            )
        )
    return ommers


class T8N(Load):
    """The class that carries out the transition."""

    tracers: Final[GroupTracer | None]
    alloc: "TestingAlloc"
    env: "TestingEnvironment"
    txs: List["TestingTransaction"]
    ommers: List[Ommer]
    rejected_transactions: List[Any]
    body: Bytes
    _block_exception: Optional[str]

    def __init__(
        self,
        options: Any,
        out_file: TextIO,
        in_file: TextIO,
        cache: ForkCache,
        *,
        t8n_data: Any = None,
        exception_mapper: Optional["ExceptionMapper"] = None,
    ) -> None:
        # Lazy testing-package imports avoid a top-level cycle with
        # `execution_testing.client_clis`.
        from execution_testing.test_types import (
            Alloc as TestingAlloc,
        )
        from execution_testing.test_types import (
            Environment as TestingEnvironment,
        )
        from execution_testing.test_types import (
            Transaction as TestingTransaction,
        )

        self.out_file = out_file
        self.in_file = in_file
        self.options = options
        self.exception_mapper = exception_mapper
        forks = Hardfork.discover()

        if "stdin" in (
            options.input_env,
            options.input_alloc,
            options.input_txs,
            options.blob_parameters,
        ):
            stdin = json.load(in_file)
        else:
            stdin = None

        if t8n_data is not None:
            # ``find_fork`` reads the env block number when resolving an
            # exception fork alias (``Paris``, ``ConstantinopleFix``,
            # …); in-process callers do not pass JSON inputs through
            # stdin, so synthesize the minimal stdin dict from t8n_data.
            options.input_env = "stdin"
            stdin = {
                "env": t8n_data.env.model_dump(mode="json", by_alias=True),
            }

        fork_module, self.fork_block = find_fork(forks, self.options, stdin)

        fork_criteria = None
        if self.fork_block is not None and self.fork_block != 0:
            # I can't find where `self.fork_block` is even used, and the vast
            # majority of the time it's zero anyway. Not changing the fork
            # criteria doesn't seem to break the tests, but changing it
            # introduces cloning overhead, so... pretend it didn't happen.
            fork_criteria = ByBlockNumber(self.fork_block)

        target_blobs_per_block = None
        max_blobs_per_block = None
        base_fee_update_fraction = None

        blob_parameters: Optional[Dict[str, Any]] = None
        if (
            t8n_data is not None
            and t8n_data.blob_params is not None
            and t8n_data.fork.bpo_fork()
            and t8n_data.fork != t8n_data.fork.non_bpo_ancestor()
        ):
            # In-process path: blob params come from the testing
            # ``ForkBlobSchedule``. Only BPO forks need the override —
            # they share their non-BPO ancestor's spec module. Non-BPO
            # forks (Cancun, Prague, Amsterdam, …) already carry the
            # correct schedule in their own module; forwarding the
            # override would force ``ForkCache`` to clone the fork into
            # a temp directory whenever the override values don't
            # byte-match the constants, attributing opcode coverage to
            # the clone's ``/tmp/...`` paths instead of the original
            # ``src/ethereum/forks/<fork>/`` source.
            blob_parameters = t8n_data.blob_params.model_dump(
                mode="json", by_alias=True
            )
        elif options.blob_parameters == "stdin":
            assert stdin is not None
            blob_parameters = stdin["blobParams"]
        elif options.blob_parameters is not None:
            with open(options.blob_parameters, "r") as f:
                blob_parameters = json.load(f)

        if blob_parameters is not None:
            target_blobs_per_block = parse_hex_or_int(
                blob_parameters["target"],
                U64,
            )
            max_blobs_per_block = parse_hex_or_int(
                blob_parameters["max"],
                U64,
            )
            base_fee_update_fraction = parse_hex_or_int(
                blob_parameters["baseFeeUpdateFraction"],
                Uint,
            )

        fork = cache.get(
            fork_module,
            fork_criteria,
            blob_schedule_target=target_blobs_per_block,
            blob_schedule_max=max_blobs_per_block,
            blob_base_fee_update_fraction=base_fee_update_fraction,
        )

        tracers = GroupTracer()

        if self.options.trace:
            trace_memory = getattr(self.options, "trace.memory", False)
            trace_stack = not getattr(self.options, "trace.nostack", False)
            trace_return_data = getattr(self.options, "trace.returndata")
            tracers.add(
                Eip3155Tracer(
                    trace_memory=trace_memory,
                    trace_stack=trace_stack,
                    trace_return_data=trace_return_data,
                    output_basedir=self.options.output_basedir,
                )
            )

        if self.options.opcode_count is not None:
            tracers.add(CountTracer())

        maybe_tracers: GroupTracer | None
        if tracers.tracers:
            trace.set_evm_trace(tracers)
            maybe_tracers = tracers
        else:
            maybe_tracers = None

        self.tracers = maybe_tracers

        self.logger = get_stream_logger("T8N")

        super().__init__(fork)

        self.chain_id = parse_hex_or_int(self.options.state_chainid, U64)

        if t8n_data is not None:
            # In-process path: caller hands the testing pydantic types
            # directly. Take a defensive copy of the input alloc so
            # ``apply_diff`` (and any other in-place mutation) never
            # escapes into the caller's Python object — multi-block
            # tests rely on the previous block's alloc staying intact
            # when the current block is invalid.
            from execution_testing.client_clis.cli_types import LazyAlloc

            raw_alloc = t8n_data.alloc
            input_alloc = (
                raw_alloc.get()
                if isinstance(raw_alloc, LazyAlloc)
                else raw_alloc
            )
            self.alloc = input_alloc.model_copy(deep=True)
            self.env = t8n_data.env
            self.txs = list(t8n_data.txs)
            self.ommers = []
            self.body = Bytes(rlp.encode([tx.rlp() for tx in self.txs]))
        else:
            # CLI / JSON path: parse the JSON inputs and validate into
            # testing pydantic types.
            raw_alloc_json = _read_json_input(
                self.options.input_alloc, stdin, "alloc"
            )
            raw_env_json = _read_json_input(
                self.options.input_env, stdin, "env"
            )
            raw_txs_json = _read_json_input(
                self.options.input_txs, stdin, "txs"
            )

            self.alloc = TestingAlloc.model_validate(raw_alloc_json)
            self.env = TestingEnvironment.model_validate(raw_env_json)
            self.txs, self.body = self._parse_txs_input(
                raw_txs_json, TestingTransaction
            )
            self.ommers = _parse_ommers_from_env_json(raw_env_json, self.fork)

        self.rejected_transactions = []

    def _parse_txs_input(
        self,
        raw_txs_json: Any,
        transaction_cls: Type["TestingTransaction"],
    ) -> tuple[List["TestingTransaction"], Bytes]:
        """
        Parse the `txs` input into testing `Transaction`s and an RLP body.

        Supports the JSON-array shape used by the CLI fixtures and the
        testing in-process caller. RLP-string input (a single hex string)
        is not supported via this path — surface a clear error rather
        than silently dropping txs.
        """
        if raw_txs_json is None:
            return [], Bytes(b"")
        if isinstance(raw_txs_json, str):
            raise NotImplementedError(
                "RLP-encoded `txs` input is not supported by the testing "
                "T8N entry point; provide a JSON array instead."
            )

        # EIP-155 ("protected") signatures only exist from Spurious Dragon
        # onwards; pre-EIP-155 forks must sign with v ∈ {27, 28}. The
        # testing ``Transaction`` model defaults ``protected=True`` and
        # would otherwise produce ``v ≥ 35`` even on Homestead.
        fork_supports_eip155 = hasattr(
            self.fork._module("transactions"), "signing_hash_155"
        )

        normalized = [T8N._normalize_tx_json(dict(tx)) for tx in raw_txs_json]
        txs: List["TestingTransaction"] = []
        for tx_dict in normalized:
            tx = transaction_cls.model_validate(tx_dict)
            # A JSON tx that carries ``secretKey`` but no ``v``/``r``/``s``
            # is unsigned; the testing model does not auto-sign in
            # ``model_post_init`` (only ``AuthorizationTuple`` does). Sign
            # it here so downstream signature recovery succeeds.
            if "v" not in tx.model_fields_set and tx.secret_key is not None:
                if not fork_supports_eip155 and int(tx.ty) == 0:
                    tx.protected = False
                tx.sign()
            txs.append(tx)
        body = Bytes(rlp.encode([tx.rlp() for tx in txs]))
        return txs, body

    @staticmethod
    def _normalize_tx_json(tx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Drop fields that the testing ``Transaction`` model rejects.

        Two boundary mismatches to smooth over:

        1. ``yParity`` on authorization tuples. The testing
           ``AuthorizationTuple`` serializer emits both ``v`` and
           ``yParity`` (they are guaranteed equal — see the model's
           ``duplicate_v_as_y_parity``), but its validator binds only
           ``v`` and treats ``yParity`` as an extra-forbidden field.
        2. ``secretKey`` on an already-signed tx. The testing
           ``Transaction`` retains the private key after auto-signing in
           ``model_post_init``, so the dump still carries ``secretKey``
           alongside the populated ``v``/``r``/``s``. On re-validation
           the model rejects the pair with ``InvalidSignaturePrivateKeyError``.
           Strip ``secretKey`` whenever ``v`` is set (i.e. the tx is
           already signed).
        """
        auth_list = tx.get("authorizationList")
        if isinstance(auth_list, list):
            tx["authorizationList"] = [
                {k: v for k, v in entry.items() if k != "yParity"}
                if isinstance(entry, dict)
                else entry
                for entry in auth_list
            ]
        if "secretKey" in tx and tx.get("v") is not None:
            tx = {k: v for k, v in tx.items() if k != "secretKey"}
        return tx

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
            ommers=tuple(self.ommers),
            state_test=self.options.state_test,
        )
        self._block_state = block_env.state
        return block_env

    def convert_transaction(self, tx: "TestingTransaction") -> Any:
        """
        Convert a testing ``Transaction`` into the fork's tx object.

        Goes via ``TransactionLoad`` (the JSON loader) rather than
        ``rlp.decode_to``: typed transactions that are structurally
        valid at the JSON level but invalid for the fork's tx type —
        e.g. a contract-creating ``BlobTransaction`` (``to=None``) —
        must still be constructed so that ``check_transaction`` inside
        ``process_transaction`` can raise the canonical
        ``TransactionTypeContractCreationError``. The RLP path rejects
        them up front with a structural ``DecodingError``, which the
        testing exception mapper has no entry for.
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

        if not self.fork.proof_of_stake:
            if self.options.state_reward is None:
                self.pay_block_rewards(self.fork.BLOCK_REWARD, block_env)
            elif self.options.state_reward != -1:
                self.pay_block_rewards(
                    U256(self.options.state_reward), block_env
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

    def run(self) -> int:
        """Run the transition and provide the relevant outputs."""
        # Clear files that may have been created in a previous
        # run of the t8n tool.
        # Define the specific files and pattern to delete
        files_to_delete = [
            self.options.output_result,
            self.options.output_alloc,
            self.options.output_body,
        ]
        pattern_to_delete = "trace-*.jsonl"

        # Iterate through the directory
        for file in os.listdir(self.options.output_basedir):
            file_path = os.path.join(self.options.output_basedir, file)

            # Check if the file matches the specific names or the pattern
            if file in files_to_delete or fnmatch.fnmatch(
                file, pattern_to_delete
            ):
                os.remove(file_path)

        try:
            if self.options.state_test:
                self.run_state_test()
            else:
                self.run_blockchain_test()
        except FatalError as e:
            self.logger.error(str(e))
            return 1

        # Mutate the alloc into the post-state for output.
        diff = self.fork.extract_block_diff(self._block_state)
        self.alloc.apply_diff(diff)

        json_state = self.alloc.model_dump(mode="json", by_alias=True)
        json_result = self.result.model_dump(
            mode="json", by_alias=True, exclude_none=True
        )

        json_output: dict[str, object] = {}

        if self.options.output_body == "stdout":
            json_output["body"] = "0x" + self.body.hex()
        elif self.options.output_body is not None:
            txs_rlp_path = os.path.join(
                self.options.output_basedir,
                self.options.output_body,
            )
            with open(txs_rlp_path, "w") as f:
                json.dump("0x" + self.body.hex(), f)
            self.logger.info(f"Wrote transaction rlp to {txs_rlp_path}")

        if self.options.output_alloc == "stdout":
            json_output["alloc"] = json_state
        else:
            alloc_output_path = os.path.join(
                self.options.output_basedir,
                self.options.output_alloc,
            )
            with open(alloc_output_path, "w") as f:
                json.dump(json_state, f, indent=4)
            self.logger.info(f"Wrote alloc to {alloc_output_path}")

        if self.options.output_result == "stdout":
            json_output["result"] = json_result
        else:
            result_output_path = os.path.join(
                self.options.output_basedir,
                self.options.output_result,
            )
            with open(result_output_path, "w") as f:
                json.dump(json_result, f, indent=4)
            self.logger.info(f"Wrote result to {result_output_path}")

        if self.options.opcode_count == "stdout":
            opcode_count_results = self._tracer(CountTracer).results()
            json_output["opcodeCount"] = opcode_count_results

            # Also attach the counts to the in-memory result for the
            # in-process caller. ``json_result`` was rendered above, so
            # the CLI JSON contract keeps ``opcodeCount`` at the top
            # level only.
            from execution_testing.client_clis.cli_types import OpcodeCount

            self.result.opcode_count = OpcodeCount.model_validate(
                opcode_count_results
            )
        elif self.options.opcode_count is not None:
            opcode_count_results = self._tracer(CountTracer).results()
            result_output_path = os.path.join(
                self.options.output_basedir,
                self.options.opcode_count,
            )
            with open(result_output_path, "w") as f:
                json.dump(opcode_count_results, f, indent=4)
            self.logger.info(f"Wrote opcode counts to {result_output_path}")

        if json_output:
            json.dump(json_output, self.out_file, indent=4)

        return 0
