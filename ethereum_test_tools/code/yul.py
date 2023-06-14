"""
Yul frontend
"""

import re
from pathlib import Path
from shutil import which
from subprocess import PIPE, run
from typing import Mapping, Optional, Tuple, Type, Union

from ethereum_test_forks import Fork

from .code import Code

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

    def __init__(
        self,
        source: str,
        fork: Optional[Fork] = None,
        binary: Optional[Path | str] = None,
    ):
        self.source = source
        self.evm_version = get_evm_version_from_fork(fork)
        if binary is None:
            which_path = which("solc")
            if which_path is not None:
                binary = Path(which_path)
        if binary is None or not Path(binary).exists():
            raise Exception(
                """`solc` binary executable not found, please refer to
                https://docs.soliditylang.org/en/latest/installing-solidity.html
                for help downloading and installing `solc`"""
            )
        self.binary = Path(binary)

    def assemble(self) -> bytes:
        """
        Assembles using `solc --assemble`.
        """
        if not self.compiled:
            solc_args: Tuple[Union[Path, str], ...] = ()
            if self.evm_version:
                solc_args = (
                    self.binary,
                    "--evm-version",
                    self.evm_version,
                    *DEFAULT_SOLC_ARGS,
                )
            else:
                solc_args = (self.binary, *DEFAULT_SOLC_ARGS)
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

    def version(self) -> str:
        """
        Return solc's version string
        """
        result = run(
            [self.binary, "--version"],
            stdout=PIPE,
            stderr=PIPE,
        )
        solc_output = result.stdout.decode().split("\n")
        version_pattern = r"0\.\d+\.\d+\+\S+"
        solc_version_string = None
        for line in solc_output:
            match = re.search(version_pattern, line)
            if match:
                solc_version_string = match.group(0)
                break
        return solc_version_string


YulCompiler = Type[Yul]
