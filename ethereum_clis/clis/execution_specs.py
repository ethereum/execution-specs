"""
Ethereum Specs EVM Resolver Transition Tool Interface.

https://github.com/petertdavies/ethereum-spec-evm-resolver
"""

import os
import re
import subprocess
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional

from ethereum_test_exceptions import (
    EOFException,
    ExceptionMapper,
    ExceptionMessage,
    TransactionException,
)
from ethereum_test_forks import Fork

from ..transition_tool import TransitionTool

DAEMON_STARTUP_TIMEOUT_SECONDS = 5


class ExecutionSpecsTransitionTool(TransitionTool):
    """
    Ethereum Specs EVM Resolver `ethereum-spec-evm-resolver` Transition Tool wrapper class.

    `ethereum-spec-evm-resolver` is installed by default for `execution-spec-tests`:
    ```console
    uv run fill --evm-bin=ethereum-spec-evm-resolver
    ```

    To use a specific version of the `ethereum-spec-evm-resolver` tool, update it to the
    desired version in `pyproject.toml`.

    The `ethereum-spec-evm-resolver` tool essentially wraps around the EELS evm daemon. It can
    handle requests for different EVM forks, even when those forks are implemented by different
    versions of EELS hosted in different places.
    """

    default_binary = Path("ethereum-spec-evm-resolver")
    detect_binary_pattern = re.compile(r"^ethereum-spec-evm-resolver\b")
    t8n_use_server: bool = True
    server_dir: Optional[TemporaryDirectory] = None

    def __init__(
        self,
        *,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the Ethereum Specs EVM Resolver Transition Tool interface."""
        os.environ.setdefault("NO_PROXY", "*")  # Disable proxy for local connections
        super().__init__(
            exception_mapper=ExecutionSpecsExceptionMapper(), binary=binary, trace=trace
        )
        args = [str(self.binary), "--help"]
        try:
            result = subprocess.run(args, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise Exception(
                "ethereum-spec-evm-resolver process unexpectedly returned a non-zero status code: "
                f"{e}."
            ) from e
        except Exception as e:
            raise Exception(
                f"Unexpected exception calling ethereum-spec-evm-resolver: {e}."
            ) from e
        self.help_string = result.stdout

    def start_server(self):
        """
        Start the t8n-server process, extract the port, and leave it running
        for future re-use.
        """
        self.server_dir = TemporaryDirectory()
        self.server_file_path = Path(self.server_dir.name) / "t8n.sock"
        replaced_str = str(self.server_file_path).replace("/", "%2F")
        self.server_url = f"http+unix://{replaced_str}/"
        self.process = subprocess.Popen(
            args=[
                str(self.binary),
                "daemon",
                "--uds",
                self.server_file_path,
            ],
        )
        start = time.time()
        while True:
            if self.server_file_path.exists():
                break
            if time.time() - start > DAEMON_STARTUP_TIMEOUT_SECONDS:
                raise Exception("Failed starting ethereum-spec-evm subprocess")
            time.sleep(0)  # yield to other processes

    def shutdown(self):
        """Stop the t8n-server process if it was started."""
        if self.process:
            self.process.terminate()
        if self.server_dir:
            self.server_dir.cleanup()
            self.server_dir = None

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Return True if the fork is supported by the tool.

        If the fork is a transition fork, we want to check the fork it transitions to.

        `ethereum-spec-evm` appends newlines to forks in the help string.
        """
        return (fork.transition_tool_name() + "\n") in self.help_string

    def _generate_post_args(
        self, t8n_data: TransitionTool.TransitionToolData
    ) -> Dict[str, List[str] | str]:
        """
        Generate the arguments for the POST request to the t8n-server.

        EELS T8N expects `--state-test` when running a state test.
        """
        return {"arg": "--state-test"} if t8n_data.state_test else {}


class ExecutionSpecsExceptionMapper(ExceptionMapper):
    """Translate between EEST exceptions and error strings returned by ExecutionSpecs."""

    @property
    def _mapping_data(self):
        return [
            ExceptionMessage(
                TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST,
                "Failed transaction: InvalidBlock()",
            ),
            ExceptionMessage(
                TransactionException.SENDER_NOT_EOA,
                "Failed transaction: InvalidSenderError('not EOA')",
            ),
            ExceptionMessage(
                TransactionException.TYPE_4_TX_CONTRACT_CREATION,
                "Failed transaction: ",
            ),
            ExceptionMessage(
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                "ailed transaction: ",
            ),
            ExceptionMessage(
                TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED,
                "iled transaction: ",
            ),
            ExceptionMessage(
                TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS,
                "led transaction: ",
            ),
            ExceptionMessage(
                TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS,
                "ed transaction: ",
            ),
            ExceptionMessage(
                TransactionException.TYPE_3_TX_PRE_FORK,
                "module 'ethereum.shanghai.transactions' has no attribute 'BlobTransaction'",
            ),
            ExceptionMessage(
                TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH,
                "d transaction: ",
            ),
            # This message is the same as TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED
            ExceptionMessage(
                TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED,
                " transaction: ",
            ),
            ExceptionMessage(
                TransactionException.TYPE_3_TX_ZERO_BLOBS,
                "transaction: ",
            ),
            ExceptionMessage(
                TransactionException.INTRINSIC_GAS_TOO_LOW,
                "ransaction: ",
            ),
            ExceptionMessage(
                TransactionException.INITCODE_SIZE_EXCEEDED,
                "ansaction: ",
            ),
            ExceptionMessage(
                TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS,
                "nsaction: ",
            ),
            ExceptionMessage(
                TransactionException.NONCE_MISMATCH_TOO_HIGH,
                "saction: ",
            ),
            ExceptionMessage(
                TransactionException.NONCE_MISMATCH_TOO_LOW,
                "action: ",
            ),
            # TODO EVMONE needs to differentiate when the section is missing in the header or body
            ExceptionMessage(EOFException.MISSING_STOP_OPCODE, "err: no_terminating_instruction"),
            ExceptionMessage(EOFException.MISSING_CODE_HEADER, "err: code_section_missing"),
            ExceptionMessage(EOFException.MISSING_TYPE_HEADER, "err: type_section_missing"),
            # TODO EVMONE these exceptions are too similar, this leeds to ambiguity
            ExceptionMessage(EOFException.MISSING_TERMINATOR, "err: header_terminator_missing"),
            ExceptionMessage(
                EOFException.MISSING_HEADERS_TERMINATOR, "err: section_headers_not_terminated"
            ),
            ExceptionMessage(EOFException.INVALID_VERSION, "err: eof_version_unknown"),
            ExceptionMessage(
                EOFException.INVALID_NON_RETURNING_FLAG, "err: invalid_non_returning_flag"
            ),
            ExceptionMessage(EOFException.INVALID_MAGIC, "err: invalid_prefix"),
            ExceptionMessage(
                EOFException.INVALID_FIRST_SECTION_TYPE, "err: invalid_first_section_type"
            ),
            ExceptionMessage(
                EOFException.INVALID_SECTION_BODIES_SIZE, "err: invalid_section_bodies_size"
            ),
            ExceptionMessage(
                EOFException.INVALID_TYPE_SECTION_SIZE, "err: invalid_type_section_size"
            ),
            ExceptionMessage(EOFException.INCOMPLETE_SECTION_SIZE, "err: incomplete_section_size"),
            ExceptionMessage(
                EOFException.INCOMPLETE_SECTION_NUMBER, "err: incomplete_section_number"
            ),
            ExceptionMessage(EOFException.TOO_MANY_CODE_SECTIONS, "err: too_many_code_sections"),
            ExceptionMessage(EOFException.ZERO_SECTION_SIZE, "err: zero_section_size"),
            ExceptionMessage(EOFException.MISSING_DATA_SECTION, "err: data_section_missing"),
            ExceptionMessage(EOFException.UNDEFINED_INSTRUCTION, "err: undefined_instruction"),
            ExceptionMessage(
                EOFException.INPUTS_OUTPUTS_NUM_ABOVE_LIMIT, "err: inputs_outputs_num_above_limit"
            ),
            ExceptionMessage(
                EOFException.UNREACHABLE_INSTRUCTIONS, "err: unreachable_instructions"
            ),
            ExceptionMessage(
                EOFException.INVALID_RJUMP_DESTINATION, "err: invalid_rjump_destination"
            ),
            ExceptionMessage(
                EOFException.UNREACHABLE_CODE_SECTIONS, "err: unreachable_code_sections"
            ),
            ExceptionMessage(EOFException.STACK_UNDERFLOW, "err: stack_underflow"),
            ExceptionMessage(
                EOFException.MAX_STACK_HEIGHT_ABOVE_LIMIT, "err: max_stack_height_above_limit"
            ),
            ExceptionMessage(
                EOFException.STACK_HIGHER_THAN_OUTPUTS, "err: stack_higher_than_outputs_required"
            ),
            ExceptionMessage(
                EOFException.JUMPF_DESTINATION_INCOMPATIBLE_OUTPUTS,
                "err: jumpf_destination_incompatible_outputs",
            ),
            ExceptionMessage(
                EOFException.INVALID_MAX_STACK_HEIGHT, "err: invalid_max_stack_height"
            ),
            ExceptionMessage(EOFException.INVALID_DATALOADN_INDEX, "err: invalid_dataloadn_index"),
            ExceptionMessage(EOFException.TRUNCATED_INSTRUCTION, "err: truncated_instruction"),
            ExceptionMessage(
                EOFException.TOPLEVEL_CONTAINER_TRUNCATED, "err: toplevel_container_truncated"
            ),
            ExceptionMessage(EOFException.ORPHAN_SUBCONTAINER, "err: unreferenced_subcontainer"),
            ExceptionMessage(
                EOFException.CONTAINER_SIZE_ABOVE_LIMIT, "err: container_size_above_limit"
            ),
            ExceptionMessage(
                EOFException.INVALID_CONTAINER_SECTION_INDEX,
                "err: invalid_container_section_index",
            ),
            ExceptionMessage(
                EOFException.INCOMPATIBLE_CONTAINER_KIND, "err: incompatible_container_kind"
            ),
            ExceptionMessage(EOFException.STACK_HEIGHT_MISMATCH, "err: stack_height_mismatch"),
            ExceptionMessage(EOFException.TOO_MANY_CONTAINERS, "err: too_many_container_sections"),
            ExceptionMessage(
                EOFException.INVALID_CODE_SECTION_INDEX, "err: invalid_code_section_index"
            ),
        ]
