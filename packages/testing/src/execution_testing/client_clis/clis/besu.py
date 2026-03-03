"""Hyperledger Besu Transition tool frontend."""

import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import textwrap
from functools import cache
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional

import requests

from execution_testing.exceptions import (
    BlockException,
    ExceptionBase,
    ExceptionMapper,
    TransactionException,
)
from execution_testing.fixtures import (
    BlockchainFixture,
    FixtureFormat,
    StateFixture,
)
from execution_testing.forks import Fork

from ..cli_types import TransitionToolOutput
from ..ethereum_cli import EthereumCLI
from ..fixture_consumer_tool import FixtureConsumerTool
from ..transition_tool import (
    Profiler,
    TransitionTool,
    dump_files_to_directory,
    model_dump_config,
)

BESU_BIN_DETECT_PATTERN = re.compile(r"^Besu evm .*$")


class BesuEvmTool(EthereumCLI):
    """Besu `evmtool` base class."""

    default_binary = Path("evmtool")
    detect_binary_pattern = BESU_BIN_DETECT_PATTERN
    cached_version: Optional[str] = None
    trace: bool

    def __init__(
        self,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the BesuEvmTool class."""
        self.binary = binary if binary else self.default_binary
        self.trace = trace

    def _run_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        try:
            return subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise Exception("Command failed with non-zero status.") from e
        except Exception as e:
            raise Exception("Unexpected exception calling evmtool.") from e

    def _consume_debug_dump(
        self,
        command: List[str],
        result: subprocess.CompletedProcess,
        fixture_path: Path,
        debug_output_path: Path,
    ) -> None:
        """Dump debug output for a consume command."""
        assert all(isinstance(x, str) for x in command), (
            f"Not all elements of 'command' list are strings: {command}"
        )
        assert len(command) > 0

        debug_fixture_path = str(debug_output_path / "fixtures.json")
        command[-1] = debug_fixture_path

        consume_direct_call = " ".join(shlex.quote(arg) for arg in command)

        consume_direct_script = textwrap.dedent(
            f"""\
            #!/bin/bash
            {consume_direct_call}
            """
        )
        dump_files_to_directory(
            debug_output_path,
            {
                "consume_direct_args.py": command,
                "consume_direct_returncode.txt": result.returncode,
                "consume_direct_stdout.txt": result.stdout,
                "consume_direct_stderr.txt": result.stderr,
                "consume_direct.sh+x": consume_direct_script,
            },
        )
        shutil.copyfile(fixture_path, debug_fixture_path)


class BesuTransitionTool(TransitionTool):
    """Besu EvmTool Transition tool frontend wrapper class."""

    default_binary = Path("evm")
    detect_binary_pattern = BESU_BIN_DETECT_PATTERN
    binary: Path
    cached_version: Optional[str] = None
    trace: bool
    process: Optional[subprocess.Popen] = None
    server_url: str
    besu_trace_dir: Optional[tempfile.TemporaryDirectory]

    supports_xdist: ClassVar[bool] = False

    def __init__(
        self,
        *,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the BesuTransitionTool class."""
        super().__init__(
            exception_mapper=BesuExceptionMapper(), binary=binary, trace=trace
        )
        args = [str(self.binary), "t8n", "--help"]
        try:
            result = subprocess.run(args, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise Exception(
                "evm process unexpectedly returned a non-zero status "
                f"code: {e}."
            ) from e
        except Exception as e:
            raise Exception(
                f"Unexpected exception calling evm tool: {e}."
            ) from e
        self.help_string = result.stdout
        self.besu_trace_dir = (
            tempfile.TemporaryDirectory() if self.trace else None
        )

    def start_server(self) -> None:
        """
        Start the t8n-server process, extract the port, and leave it
        running for future reuse.
        """
        args = [
            str(self.binary),
            "t8n-server",
            "--port=0",  # OS assigned server port
        ]

        if self.trace:
            args.append("--trace")
            if self.besu_trace_dir:
                args.append(f"--output.basedir={self.besu_trace_dir.name}")

        self.process = subprocess.Popen(
            args=args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        while True:
            if self.process.stdout is None:
                raise Exception("Failed starting Besu subprocess")
            line = str(self.process.stdout.readline())

            if not line or "Failed to start transition server" in line:
                raise Exception("Failed starting Besu subprocess\n" + line)
            if "Transition server listening on" in line:
                match = re.search(
                    "Transition server listening on (\\d+)", line
                )
                if match:
                    port = match.group(1)
                    self.server_url = f"http://localhost:{port}/"
                    break

    def shutdown(self) -> None:
        """Stop the t8n-server process if it was started."""
        if self.process:
            self.process.kill()
        if self.besu_trace_dir:
            self.besu_trace_dir.cleanup()

    def _evaluate(
        self,
        *,
        transition_tool_data: TransitionTool.TransitionToolData,
        debug_output_path: Path | None,
        slow_request: bool,
        profiler: Profiler,
    ) -> TransitionToolOutput:
        """Execute `evm t8n` with the specified arguments."""
        del slow_request, profiler

        if not self.process:
            self.start_server()

        input_json = transition_tool_data.to_input().model_dump(
            mode="json", **model_dump_config
        )

        state_json = {
            "fork": transition_tool_data.fork_name,
            "chainid": transition_tool_data.chain_id,
            "reward": transition_tool_data.reward,
        }

        post_data = {"state": state_json, "input": input_json}

        if debug_output_path:
            post_data_string = json.dumps(post_data, indent=4)
            additional_indent = " " * 16  # for pretty indentation in t8n.sh
            indented_post_data_string = "{\n" + "\n".join(
                additional_indent + line
                for line in post_data_string[1:].splitlines()
            )
            t8n_script = textwrap.dedent(
                f"""\
                #!/bin/bash
                # Use $1 as t8n-server port if provided, else default to 3000
                PORT=${{1:-3000}}
                curl http://localhost:${{PORT}}/ -X POST \\
                -H "Content-Type: application/json" \\
                --data '{indented_post_data_string}'
                """
            )
            dump_files_to_directory(
                debug_output_path,
                {
                    "state.json": state_json,
                    "input/alloc.json": input_json["alloc"],
                    "input/env.json": input_json["env"],
                    "input/txs.json": input_json["txs"],
                    "t8n.sh+x": t8n_script,
                },
            )

        response = requests.post(self.server_url, json=post_data, timeout=5)
        # exception visible in pytest failure output
        response.raise_for_status()
        output: TransitionToolOutput = TransitionToolOutput.model_validate(
            response.json(),
            context={"exception_mapper": self.exception_mapper},
        )

        if debug_output_path:
            dump_files_to_directory(
                debug_output_path,
                {
                    "response.txt": response.text,
                    "status_code.txt": response.status_code,
                    "time_elapsed_seconds.txt": (
                        response.elapsed.total_seconds()
                    ),
                },
            )

        if response.status_code != 200:
            raise Exception(
                f"t8n-server returned status code {response.status_code}, "
                f"response: {response.text}"
            )

        if debug_output_path:
            dump_files_to_directory(
                debug_output_path,
                {
                    "output/alloc.json": output.alloc.raw,
                    "output/result.json": output.result.model_dump(
                        mode="json", **model_dump_config
                    ),
                    "output/txs.rlp": str(output.body),
                },
            )

        if self.trace and self.besu_trace_dir:
            self.collect_traces(
                output.result.receipts, self.besu_trace_dir, debug_output_path
            )
            for i, r in enumerate(output.result.receipts):
                trace_file_name = f"trace-{i}-{r.transaction_hash}.jsonl"
                os.remove(
                    os.path.join(self.besu_trace_dir.name, trace_file_name)
                )

        return output

    def is_fork_supported(self, fork: Fork) -> bool:
        """Return True if the fork is supported by the tool."""
        return fork.transition_tool_name() in self.help_string


class BesuExceptionMapper(ExceptionMapper):
    """Translate between EEST exceptions and error strings returned by Besu."""

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.NONCE_IS_MAX: "invalid Nonce must be less than",
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            "transaction invalid tx max fee per blob gas less than "
            "block blob gas fee"
        ),
        TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW: (
            "invalid Upfront gas cost cannot exceed 2^256 Wei"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            "transaction invalid gasPrice is less than the current BaseFee"
        ),
        BlockException.GAS_USED_OVERFLOW: "provided gas insufficient",
        TransactionException.GAS_ALLOWANCE_EXCEEDED: (
            "provided gas insufficient"
        ),
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "transaction invalid max priority fee per gas cannot be greater "
            "than max fee per gas"
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "Invalid versionedHash"
        ),
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            "transaction invalid transaction blob transactions must have "
            "a to address"
        ),
        TransactionException.TYPE_3_TX_WITH_FULL_BLOBS: (
            "Failed to decode transactions from block parameter"
        ),
        TransactionException.TYPE_3_TX_ZERO_BLOBS: (
            "Failed to decode transactions from block parameter"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            "Transaction type BLOB is invalid, accepted transaction types are"
        ),
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: (
            "transaction invalid transaction code delegation transactions "
            "must have a non-empty code delegation list"
        ),
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            "transaction invalid transaction code delegation transactions "
            "must have a to address"
        ),
        TransactionException.TYPE_4_TX_PRE_FORK: (
            "transaction invalid Transaction type DELEGATE_CODE is invalid"
        ),
        BlockException.RLP_STRUCTURES_ENCODING: (
            "Failed to decode transactions from block parameter"
        ),
        BlockException.INCORRECT_EXCESS_BLOB_GAS: (
            "Payload excessBlobGas does not match calculated excessBlobGas"
        ),
        BlockException.BLOB_GAS_USED_ABOVE_LIMIT: (
            "Payload BlobGasUsed does not match calculated BlobGasUsed"
        ),
        BlockException.INCORRECT_BLOB_GAS_USED: (
            "Payload BlobGasUsed does not match calculated BlobGasUsed"
        ),
        BlockException.INVALID_GAS_USED_ABOVE_LIMIT: (
            "Header validation failed (FULL)"
        ),
        BlockException.INVALID_GASLIMIT: "Header validation failed (FULL)",
        BlockException.EXTRA_DATA_TOO_BIG: "Header validation failed (FULL)",
        BlockException.INVALID_BLOCK_NUMBER: (
            "Header validation failed (FULL)"
        ),
        BlockException.INVALID_BASEFEE_PER_GAS: (
            "Header validation failed (FULL)"
        ),
        BlockException.INVALID_BLOCK_TIMESTAMP_OLDER_THAN_PARENT: (
            "block timestamp not greater than parent"
        ),
        BlockException.INVALID_LOG_BLOOM: (
            "failed to validate output of imported block"
        ),
        BlockException.INVALID_RECEIPTS_ROOT: (
            "failed to validate output of imported block"
        ),
        BlockException.INVALID_STATE_ROOT: (
            "World State Root does not match expected value"
        ),
    }
    mapping_regex = {
        BlockException.INVALID_REQUESTS: (
            r"Invalid execution requests|Requests hash mismatch, "
            r"calculated: 0x[0-9a-f]+ header: 0x[0-9a-f]+"
        ),
        BlockException.INVALID_BLOCK_HASH: (
            r"Computed block hash 0x[0-9a-f]+ does not match block "
            r"hash parameter 0x[0-9a-f]+"
        ),
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: (
            r"System call halted|"
            r"System call did not execute to completion"
        ),
        BlockException.SYSTEM_CONTRACT_EMPTY: (
            r"(Invalid system call, no code at address)|"
            r"(Invalid system call address:)"
        ),
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: (
            r"Invalid (amount|index|pubKey|signature|withdrawalCred) "
            r"(offset|size): expected (\d+), but got (-?\d+)|"
            r"Invalid deposit log length\. Must be \d+ bytes, "
            r"but is \d+ bytes"
        ),
        BlockException.RLP_BLOCK_LIMIT_EXCEEDED: (
            r"Block size of \d+ bytes exceeds limit of \d+ bytes"
        ),
        TransactionException.INITCODE_SIZE_EXCEEDED: (
            r"transaction invalid Initcode size of \d+ exceeds "
            r"maximum size of \d+"
        ),
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            r"transaction invalid transaction up-front cost 0x[0-9a-f]+ "
            r"exceeds transaction sender account balance 0x[0-9a-f]+"
        ),
        TransactionException.INTRINSIC_GAS_TOO_LOW: (
            r"transaction invalid intrinsic gas cost \d+ "
            r"exceeds gas limit \d+"
        ),
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: (
            r"transaction invalid intrinsic gas cost \d+ "
            r"exceeds gas limit \d+"
        ),
        TransactionException.SENDER_NOT_EOA: (
            r"transaction invalid Sender 0x[0-9a-f]+ has deployed code "
            r"and so is not authorized to send transactions"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: (
            r"transaction invalid transaction nonce \d+ "
            r"below sender account nonce \d+"
        ),
        TransactionException.NONCE_MISMATCH_TOO_HIGH: (
            r"transaction invalid transaction nonce \d+ "
            r"does not match sender account nonce \d+"
        ),
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: (
            r"transaction invalid Transaction gas limit "
            r"must be at most \d+"
        ),
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            r"Blob transaction 0x[0-9a-f]+ exceeds "
            r"block blob gas limit: \d+ > \d+"
        ),
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: (
            r"Blob transaction has too many blobs: \d+|"
            r"Invalid Blob Count: \d+"
        ),
        # BAL Exceptions: TODO - review once all clients completed.
        BlockException.INVALID_BAL_EXTRA_ACCOUNT: (
            r"Block access list hash mismatch, "
            r"calculated:\s*(0x[a-f0-9]+)\s+header:\s*(0x[a-f0-9]+)"
        ),
        BlockException.INVALID_BAL_HASH: (
            r"Block access list hash mismatch, "
            r"calculated:\s*(0x[a-f0-9]+)\s+header:\s*(0x[a-f0-9]+)"
        ),
        BlockException.INVALID_BAL_MISSING_ACCOUNT: (
            r"Block access list hash mismatch, "
            r"calculated:\s*(0x[a-f0-9]+)\s+header:\s*(0x[a-f0-9]+)"
        ),
        BlockException.INVALID_BLOCK_ACCESS_LIST: (
            r"Block access list hash mismatch, "
            r"calculated:\s*(0x[a-f0-9]+)\s+header:\s*(0x[a-f0-9]+)|"
            r"Block access list validation failed for block"
        ),
        BlockException.INCORRECT_BLOCK_FORMAT: (
            r"Block access list hash mismatch, "
            r"calculated:\s*(0x[a-f0-9]+)\s+header:\s*(0x[a-f0-9]+)"
        ),
    }


class BesuFixtureConsumer(
    BesuEvmTool,
    FixtureConsumerTool,
    fixture_formats=[StateFixture, BlockchainFixture],
):
    """Besu's implementation of the fixture consumer."""

    def consume_blockchain_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """
        Consume a single blockchain test.

        Besu's ``evmtool block-test`` accepts ``--test-name`` to
        select a specific fixture from the file.
        """
        subcommand = "block-test"
        subcommand_options: List[str] = []
        if debug_output_path:
            subcommand_options += ["--json"]

        if fixture_name:
            subcommand_options += [
                "--test-name",
                fixture_name,
            ]

        command = (
            [str(self.binary)]
            + [subcommand]
            + subcommand_options
            + [str(fixture_path)]
        )

        result = self._run_command(command)

        if debug_output_path:
            self._consume_debug_dump(
                command, result, fixture_path, debug_output_path
            )

        if result.returncode != 0:
            raise Exception(
                f"Unexpected exit code:\n{' '.join(command)}\n\n"
                f"Error:\n{result.stderr}"
            )

        # Parse text output for failures
        stdout = result.stdout
        if "Failed:" in stdout:
            failed_match = re.search(r"Failed:\s+(\d+)", stdout)
            if failed_match and int(failed_match.group(1)) > 0:
                raise Exception(f"Blockchain test failed:\n{stdout}")

    @cache  # noqa
    def consume_state_test_file(
        self,
        fixture_path: Path,
        debug_output_path: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """
        Consume an entire state test file.

        Besu's ``evmtool state-test`` outputs one JSON object per
        line (NDJSON) with a ``test`` field instead of ``name``.
        This method normalizes the output to match the expected
        format.
        """
        subcommand = "state-test"
        subcommand_options: List[str] = []
        if debug_output_path:
            subcommand_options += ["--json"]

        command = (
            [str(self.binary)]
            + [subcommand]
            + subcommand_options
            + [str(fixture_path)]
        )
        result = self._run_command(command)

        if debug_output_path:
            self._consume_debug_dump(
                command, result, fixture_path, debug_output_path
            )

        if result.returncode != 0:
            raise Exception(
                f"Unexpected exit code:\n{' '.join(command)}\n\n"
                f"Error:\n{result.stderr}"
            )

        # Parse NDJSON output, normalize "test" -> "name"
        results: List[Dict[str, Any]] = []
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if "test" in entry and "name" not in entry:
                    entry["name"] = entry["test"]
                results.append(entry)
            except json.JSONDecodeError as e:
                raise Exception(
                    f"Failed to parse Besu state-test output as JSON.\n"
                    f"Offending line:\n{line}\n\n"
                    f"Error: {e}"
                ) from e
        return results

    def consume_state_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """
        Consume a single state test.

        Uses the cached result from ``consume_state_test_file``
        and selects the requested fixture by name.
        """
        file_results = self.consume_state_test_file(
            fixture_path=fixture_path,
            debug_output_path=debug_output_path,
        )
        if fixture_name:
            test_result = [
                r for r in file_results if r["name"] == fixture_name
            ]
            assert len(test_result) < 2, (
                f"Multiple test results for {fixture_name}"
            )
            assert len(test_result) == 1, (
                f"Test result for {fixture_name} missing"
            )
            assert test_result[0]["pass"], (
                f"State test failed: "
                f"{test_result[0].get('error', 'unknown error')}"
            )
        else:
            if any(not r["pass"] for r in file_results):
                exception_text = "State test failed: \n" + "\n".join(
                    f"{r['name']}: " + r.get("error", "unknown error")
                    for r in file_results
                    if not r["pass"]
                )
                raise Exception(exception_text)

    def consume_fixture(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """
        Execute the appropriate Besu fixture consumer for the
        fixture at ``fixture_path``.
        """
        if fixture_format == BlockchainFixture:
            self.consume_blockchain_test(
                fixture_path=fixture_path,
                fixture_name=fixture_name,
                debug_output_path=debug_output_path,
            )
        elif fixture_format == StateFixture:
            self.consume_state_test(
                fixture_path=fixture_path,
                fixture_name=fixture_name,
                debug_output_path=debug_output_path,
            )
        else:
            raise Exception(
                f"Fixture format {fixture_format.format_name} "
                f"not supported by {self.binary}"
            )
