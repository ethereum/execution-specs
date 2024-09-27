"""
Ethereum Specs EVM Resolver Transition Tool Interface.

https://github.com/petertdavies/ethereum-spec-evm-resolver
"""

import subprocess
import time
from pathlib import Path
from re import compile
from tempfile import TemporaryDirectory
from typing import Optional

from ethereum_test_forks import Fork

from .transition_tool import TransitionTool

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
    detect_binary_pattern = compile(r"^ethereum-spec-evm-resolver\b")
    t8n_use_server: bool = True
    server_dir: Optional[TemporaryDirectory] = None

    def __init__(
        self,
        *,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        super().__init__(binary=binary, trace=trace)
        args = [str(self.binary), "--help"]
        try:
            result = subprocess.run(args, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise Exception(
                "ethereum-spec-evm-resolver process unexpectedly returned a non-zero status code: "
                f"{e}."
            )
        except Exception as e:
            raise Exception(f"Unexpected exception calling ethereum-spec-evm-resolver: {e}.")
        self.help_string = result.stdout

    def start_server(self):
        """
        Starts the t8n-server process, extracts the port, and leaves it running for future re-use.
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
        """
        Stops the t8n-server process if it was started.
        """
        if self.process:
            self.process.terminate()
        if self.server_dir:
            self.server_dir.cleanup()
            self.server_dir = None

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Returns True if the fork is supported by the tool.

        If the fork is a transition fork, we want to check the fork it transitions to.

        `ethereum-spec-evm` appends newlines to forks in the help string.
        """
        return (fork.transition_tool_name() + "\n") in self.help_string
