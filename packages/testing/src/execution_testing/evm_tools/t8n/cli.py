"""
CLI / JSON wrapper for the ``T8N`` transition tool.

``T8N`` itself consumes a testing-package
``TransitionTool.TransitionToolData`` and knows nothing about argparse,
stdin/stdout, or JSON. This module provides the bridge used by the
``ethereum-spec-evm t8n`` entry point and by ``statetest``:

* :func:`build_t8n_from_cli_options` reads the JSON inputs
  (stdin / files), resolves the fork, parses everything into testing
  pydantic types, bundles them into a ``TransitionToolData``, builds
  the tracer group, and returns a constructed ``T8N``.
* :func:`write_t8n_outputs` serialises the t8n output + opcode-count
  results to disk / stdout per ``--output.*`` flags.
* :func:`run_t8n_cli` chains the two for the CLI entry point.
"""

import argparse
import fnmatch
import json
import os
from typing import Any, Dict, List, Optional, TextIO, Tuple

from ethereum_rlp import rlp
from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.loaders.fork_loader import ForkLoad
from ethereum_spec_tools.utils import FatalError, find_fork, parse_hex_or_int
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U64

from . import T8N, ForkCache
from .block_environment import Ommer
from .evm_trace.count import CountTracer
from .evm_trace.eip3155 import Eip3155Tracer
from .evm_trace.group import GroupTracer


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
    t8n_parser.add_argument(
        "--no-stateless",
        dest="no_stateless",
        action="store_true",
        help=(
            "Skip stateless witness generation, input serialization, "
            "and guest validation."
        ),
    )


def _read_json_input(
    path_or_stdin: str, stdin: Optional[Dict], key: str
) -> Any:
    """Read one of the t8n JSON inputs (alloc / env / txs)."""
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


def _normalize_tx_json(tx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Drop fields that the testing ``Transaction`` model rejects.

    Three boundary mismatches to smooth over:

    1. ``yParity`` on authorization tuples. The testing
       ``AuthorizationTuple`` serializer emits both ``v`` and
       ``yParity`` (they are guaranteed equal — see the model's
       ``duplicate_v_as_y_parity``), but its validator binds only
       ``v`` and treats ``yParity`` as an extra-forbidden field.
    2. ``secretKey`` on an already-signed tx. The testing
       ``Transaction`` retains the private key after auto-signing in
       ``model_post_init``, so the dump still carries ``secretKey``
       alongside the populated ``v``/``r``/``s``. On re-validation
       the model rejects the pair with
       ``InvalidSignaturePrivateKeyError``. Strip ``secretKey``
       whenever ``v`` is set (i.e. the tx is already signed).
    3. A tx with no signature material at all. Filled state tests
       store a tx whose signature is deliberately invalid without
       ``v``/``r``/``s`` or ``secretKey`` (the fixture format cannot
       express explicit signature values), expecting the fork to
       reject it. Default the components to zero; leaving them unset
       would make ``Transaction.rlp`` try to auto-sign a key-less tx
       and die on an assertion.
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
    if not any(
        tx.get(key) is not None
        for key in ("secretKey", "v", "yParity", "r", "s")
    ):
        tx["v"] = "0x00"
        tx["r"] = "0x00"
        tx["s"] = "0x00"
    return tx


def _parse_txs_json_to_testing(
    raw_txs_json: Any,
    fork_module: Hardfork,
    transaction_cls: Any,
) -> Tuple[List[Any], Bytes]:
    """
    Parse a JSON tx array into signed testing ``Transaction`` objects.

    Unsigned txs carrying only ``secretKey`` are signed in place via
    ``Transaction.sign``; pre-Spurious-Dragon forks get
    ``protected=False`` so the ``v`` value stays in ``{27, 28}``.

    RLP-string input (a single hex string of an encoded tx list) is
    rejected — this path only handles JSON arrays.
    """
    if raw_txs_json is None:
        return [], Bytes(b"")
    if isinstance(raw_txs_json, str):
        raise NotImplementedError(
            "RLP-encoded `txs` input is not supported by the testing "
            "T8N entry point; provide a JSON array instead."
        )

    fork_supports_eip155 = hasattr(
        fork_module.module("transactions"), "signing_hash_155"
    )

    normalized = [_normalize_tx_json(dict(tx)) for tx in raw_txs_json]
    txs: List[Any] = []
    for tx_dict in normalized:
        tx = transaction_cls.model_validate(tx_dict)
        if "v" not in tx.model_fields_set and tx.secret_key is not None:
            if not fork_supports_eip155 and int(tx.ty) == 0:
                tx.protected = False
            tx.sign()
        txs.append(tx)
    body = Bytes(rlp.encode([tx.rlp() for tx in txs]))
    return txs, body


def _parse_blob_params_from_options(
    options: Any, stdin: Optional[Dict]
) -> Any:
    """
    Load a testing ``ForkBlobSchedule`` from ``--input.blobParams``.

    Returns ``None`` when the flag is unset. Reads from ``stdin``
    (``"blobParams"`` key) or a file path depending on the flag value.
    """
    # Function-scoped: see import-cycle note in ``result.py``.
    from execution_testing.base_types.composite_types import (
        ForkBlobSchedule,
    )

    if options.blob_parameters == "stdin":
        assert stdin is not None
        raw = stdin["blobParams"]
    elif options.blob_parameters is not None:
        with open(options.blob_parameters, "r") as f:
            raw = json.load(f)
    else:
        return None
    return ForkBlobSchedule.model_validate(raw)


def _build_tracers_from_options(
    options: Any,
) -> Optional[GroupTracer]:
    """
    Build the tracer group from CLI ``--trace*`` / ``--opcode.count``
    flags. Returns ``None`` if no tracer would be active.
    """
    tracers = GroupTracer()
    if options.trace:
        trace_memory = getattr(options, "trace.memory", False)
        trace_stack = not getattr(options, "trace.nostack", False)
        trace_return_data = getattr(options, "trace.returndata")
        tracers.add(
            Eip3155Tracer(
                trace_memory=trace_memory,
                trace_stack=trace_stack,
                trace_return_data=trace_return_data,
                output_basedir=options.output_basedir,
            )
        )
    if options.opcode_count is not None:
        tracers.add(CountTracer())
    return tracers if tracers.tracers else None


# Spec ``Hardfork.title_case_name`` matches the testing-side
# ``Fork.name()`` after stripping spaces, except for a handful of
# legacy outliers where the testing class uses a different
# capitalisation convention.
_TESTING_FORK_NAME_OVERRIDES = {
    "DaoFork": "DAOFork",
}


def _testing_fork_from_spec_hardfork(hardfork: Hardfork) -> Any:
    """Map a spec ``Hardfork`` to the matching testing ``Fork`` class."""
    # Function-scoped: see import-cycle note in ``result.py``.
    from execution_testing.forks import get_fork_by_name

    name = hardfork.title_case_name.replace(" ", "")
    name = _TESTING_FORK_NAME_OVERRIDES.get(name, name)
    fork = get_fork_by_name(name)
    if fork is None:
        raise ValueError(
            f"No testing.Fork class for spec hardfork "
            f"{hardfork.short_name!r} (looked for {name!r})"
        )
    return fork


def _resolve_state_reward(
    state_reward: Optional[int], fork_module: Hardfork
) -> int:
    """
    Resolve a CLI ``--state.reward`` value into the int that
    ``TransitionToolData.reward`` expects.

    ``None`` means "use the fork's default ``BLOCK_REWARD``"; an
    explicit ``-1`` means "skip block rewards entirely" (the testing
    sentinel); any other int passes through unchanged.
    """
    if state_reward is None:
        fork_load = ForkLoad(fork_module)
        if fork_load.proof_of_stake:
            return -1
        return int(fork_load.BLOCK_REWARD)
    return state_reward


def build_t8n_from_cli_options(
    options: Any,
    in_file: TextIO,
    cache: ForkCache,
) -> T8N:
    """
    Construct a ``T8N`` from CLI options + JSON stdin / file inputs.

    Reads ``--input.*`` files (or stdin), validates each piece into
    testing pydantic types, bundles them into a ``TransitionToolData``,
    builds the tracer group, and hands them to ``T8N``.
    """
    from execution_testing.base_types.composite_types import BlobSchedule
    from execution_testing.client_clis.transition_tool import TransitionTool
    from execution_testing.test_types import (
        Alloc as TestingAlloc,
    )
    from execution_testing.test_types import (
        Environment as TestingEnvironment,
    )
    from execution_testing.test_types import (
        Transaction as TestingTransaction,
    )

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

    fork_module, fork_block = find_fork(forks, options, stdin)
    testing_fork = _testing_fork_from_spec_hardfork(fork_module)

    raw_alloc_json = _read_json_input(options.input_alloc, stdin, "alloc")
    raw_env_json = _read_json_input(options.input_env, stdin, "env")
    raw_txs_json = _read_json_input(options.input_txs, stdin, "txs")
    blob_params = _parse_blob_params_from_options(options, stdin)

    alloc = TestingAlloc.model_validate(raw_alloc_json)
    env = TestingEnvironment.model_validate(raw_env_json)
    txs, _body = _parse_txs_json_to_testing(
        raw_txs_json, fork_module, TestingTransaction
    )

    # Wrap the single per-fork blob schedule into a ``BlobSchedule``
    # collection keyed by fork name (the field TransitionToolData
    # expects).
    blob_schedule: Any = None
    if blob_params is not None:
        blob_schedule = BlobSchedule()
        blob_schedule.append(fork=testing_fork.name(), schedule=blob_params)

    t8n_data = TransitionTool.TransitionToolData(
        alloc=alloc,
        env=env,
        txs=txs,
        fork=testing_fork,
        chain_id=int(parse_hex_or_int(options.state_chainid, U64)),
        reward=_resolve_state_reward(options.state_reward, fork_module),
        blob_schedule=blob_schedule,
        state_test=options.state_test,
        skip_stateless_validation=options.no_stateless,
    )

    # ``Ommer.address`` is parsed via the per-fork ``hex_to_address``
    # helper; construct a temporary ``ForkLoad`` from the resolved
    # module just to get the conversion.
    fork_load = ForkLoad(fork_module)
    ommers = _parse_ommers_from_env_json(raw_env_json, fork_load)

    return T8N(
        t8n_data,
        cache=cache,
        fork_block=fork_block,
        ommers=ommers,
        tracers=_build_tracers_from_options(options),
    )


def write_t8n_outputs(
    t8n: T8N,
    output: Any,
    options: Any,
    out_file: TextIO,
) -> None:
    """Serialise the t8n output + opcode counts per ``--output.*``."""
    json_state = output.alloc.materialize().model_dump(
        mode="json", by_alias=True
    )
    json_result = output.result.model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    json_output: Dict[str, object] = {}
    body_hex = "0x" + bytes(output.body or b"").hex()

    if options.output_body == "stdout":
        json_output["body"] = body_hex
    elif options.output_body is not None:
        txs_rlp_path = os.path.join(
            options.output_basedir, options.output_body
        )
        with open(txs_rlp_path, "w") as f:
            json.dump(body_hex, f)
        t8n.logger.info(f"Wrote transaction rlp to {txs_rlp_path}")

    if options.output_alloc == "stdout":
        json_output["alloc"] = json_state
    else:
        alloc_output_path = os.path.join(
            options.output_basedir, options.output_alloc
        )
        with open(alloc_output_path, "w") as f:
            json.dump(json_state, f, indent=4)
        t8n.logger.info(f"Wrote alloc to {alloc_output_path}")

    if options.output_result == "stdout":
        json_output["result"] = json_result
    else:
        result_output_path = os.path.join(
            options.output_basedir, options.output_result
        )
        with open(result_output_path, "w") as f:
            json.dump(json_result, f, indent=4)
        t8n.logger.info(f"Wrote result to {result_output_path}")

    if options.opcode_count == "stdout":
        json_output["opcodeCount"] = t8n._tracer(CountTracer).results()
    elif options.opcode_count is not None:
        result_output_path = os.path.join(
            options.output_basedir, options.opcode_count
        )
        with open(result_output_path, "w") as f:
            json.dump(t8n._tracer(CountTracer).results(), f, indent=4)
        t8n.logger.info(f"Wrote opcode counts to {result_output_path}")

    if json_output:
        json.dump(json_output, out_file, indent=4)


def _clean_output_dir(options: Any) -> None:
    """Remove prior output files matching ``--output.*`` from the basedir."""
    files_to_delete = [
        options.output_result,
        options.output_alloc,
        options.output_body,
    ]
    pattern_to_delete = "trace-*.jsonl"
    for file in os.listdir(options.output_basedir):
        file_path = os.path.join(options.output_basedir, file)
        if file in files_to_delete or fnmatch.fnmatch(file, pattern_to_delete):
            os.remove(file_path)


def run_t8n_cli(
    options: Any,
    out_file: TextIO,
    in_file: TextIO,
    cache: ForkCache,
) -> int:
    """End-to-end CLI entry: read JSON, run ``T8N``, write JSON output."""
    _clean_output_dir(options)
    t8n = build_t8n_from_cli_options(options, in_file, cache)
    try:
        output = t8n.run()
    except FatalError as e:
        t8n.logger.error(str(e))
        return 1
    write_t8n_outputs(t8n, output, options, out_file)
    return 0


__all__ = [
    "build_t8n_from_cli_options",
    "run_t8n_cli",
    "t8n_arguments",
    "write_t8n_outputs",
]
