"""
Go-ethereum Transition tool interface.
"""

import re
import subprocess
from pathlib import Path
from re import compile
from typing import Optional

from ethereum_test_forks import Fork

from .transition_tool import TransitionTool


class NimbusTransitionTool(TransitionTool):
    """
    Nimbus `evm` Transition tool interface wrapper class.
    """

    default_binary = Path("t8n")
    detect_binary_pattern = compile(r"^Nimbus-t8n\b")
    version_flag: str = "--version"

    binary: Path
    cached_version: Optional[str] = None
    trace: bool

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
            raise Exception("evm process unexpectedly returned a non-zero status code: " f"{e}.")
        except Exception as e:
            raise Exception(f"Unexpected exception calling evm tool: {e}.")
        self.help_string = result.stdout

    def version(self) -> str:
        """
        Gets `evm` binary version.
        """
        if self.cached_version is None:
            self.cached_version = re.sub(r"\x1b\[0m", "", super().version()).strip()

        return self.cached_version

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Returns True if the fork is supported by the tool.

        If the fork is a transition fork, we want to check the fork it transitions to.
        """
        return fork.fork() in self.help_string
