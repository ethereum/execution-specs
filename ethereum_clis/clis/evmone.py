"""
Evmone Transition tool interface.
"""

from pathlib import Path
from re import compile
from typing import Optional

from ethereum_test_forks import Fork

from ..transition_tool import TransitionTool


class EvmOneTransitionTool(TransitionTool):
    """
    Evmone `evmone-t8n` Transition tool interface wrapper class.
    """

    default_binary = Path("evmone-t8n")
    detect_binary_pattern = compile(r"^evmone-t8n\b")
    t8n_use_stream = False

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

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Returns True if the fork is supported by the tool.
        Currently, evmone-t8n provides no way to determine supported forks.
        """
        return True
