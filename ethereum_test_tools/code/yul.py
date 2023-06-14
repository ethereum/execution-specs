"""
Yul frontend
"""

from pathlib import Path
from subprocess import PIPE, run
from typing import Mapping, Optional, Tuple, Type

from ethereum_test_forks import Fork

from .code import Code

SOLC: Path = Path("solc")
DEFAULT_SOLC_ARGS = ("--assemble", "-")


def get_evm_version_from_fork(fork: Fork | None):
    """
    Get the solc evm version corresponding to `fork`.

    Args
    ----
        fork (Fork): The fork to retrieve the corresponding evm version for.

    Returns
    -------
        str: The name of evm version as required by solc's --evm-version.
    """
    if not fork:
        return None
    fork_to_evm_version_map: Mapping[str, str] = {"Merge": "paris"}
    if fork.name() in fork_to_evm_version_map:
        return fork_to_evm_version_map[fork.name()]
    return fork.name().lower()


class Yul(Code):
    """
    Yul compiler.
    Compiles Yul source code into bytecode.
    """

    source: str
    compiled: Optional[bytes] = None

    def __init__(self, source: str, fork: Fork = None):
        self.source = source
        self.evm_version = get_evm_version_from_fork(fork)

    def assemble(self) -> bytes:
        """
        Assembles using `solc --assemble`.
        """
        if not self.compiled:
            solc_args: Tuple[str, ...] = ()
            if self.evm_version:
                solc_args = (
                    str(SOLC),
                    "--evm-version",
                    self.evm_version,
                    *DEFAULT_SOLC_ARGS,
                )
            else:
                solc_args = (str(SOLC), *DEFAULT_SOLC_ARGS)
            result = run(
                solc_args,
                input=str.encode(self.source),
                stdout=PIPE,
                stderr=PIPE,
            )

            if result.returncode != 0:
                stderr_lines = result.stderr.decode().split("\n")
                stderr_message = "\n".join(line.strip() for line in stderr_lines)
                raise Exception(f"failed to compile yul source:\n{stderr_message[7:]}")

            lines = result.stdout.decode().split("\n")

            hex_str = lines[lines.index("Binary representation:") + 1]

            self.compiled = bytes.fromhex(hex_str)
        return self.compiled


YulCompiler = Type[Yul]
