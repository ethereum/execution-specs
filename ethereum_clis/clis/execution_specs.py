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
from typing import ClassVar, Dict, List, Optional

from ethereum_test_exceptions import (
    BlockException,
    ExceptionBase,
    ExceptionMapper,
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
    server_url: str | None = None

    def __init__(
        self,
        *,
        binary: Optional[Path] = None,
        trace: bool = False,
        server_url: str | None = None,
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
        self.server_url = server_url

    def start_server(self):
        """
        Start the t8n-server process, extract the port, and leave it running
        for future reuse.
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

    reliable: ClassVar[bool] = False
    """
    TODO: Exception messages returned from ExecutionSpecs are not reliable because most of the
    exceptions consist of the same string without indication of the particular exception type.
    """

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: "Failed transaction: InvalidBlock()",
        TransactionException.SENDER_NOT_EOA: "Failed transaction: InvalidSenderError('not EOA')",
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: "Failed transaction: ",
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: "ailed transaction: ",
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: "iled transaction: ",
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: "led transaction: ",
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: "ed transaction: ",
        TransactionException.TYPE_3_TX_PRE_FORK: (
            "module 'ethereum.shanghai.transactions' has no attribute 'BlobTransaction'"
        ),
        TransactionException.TYPE_4_TX_PRE_FORK: "Unknown transaction type: 0x4",
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: "d transaction: ",
        # This message is the same as TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: " transaction: ",
        TransactionException.TYPE_3_TX_ZERO_BLOBS: "transaction: ",
        TransactionException.INTRINSIC_GAS_TOO_LOW: "ransaction: ",
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: "ransaction: ",
        TransactionException.INITCODE_SIZE_EXCEEDED: "ansaction: ",
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: "nsaction: ",
        TransactionException.NONCE_MISMATCH_TOO_HIGH: "saction: ",
        TransactionException.NONCE_MISMATCH_TOO_LOW: "action: ",
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: "ction: ",
        TransactionException.NONCE_IS_MAX: "tion: ",
        TransactionException.GAS_ALLOWANCE_EXCEEDED: "ion: ",
        BlockException.SYSTEM_CONTRACT_EMPTY: "System contract address",
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: "call failed:",
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: "deposit",
    }
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {}
