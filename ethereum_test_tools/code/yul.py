"""
Yul frontend
"""

import re
import warnings
from pathlib import Path
from shutil import which
from subprocess import PIPE, run
from typing import Optional, Sized, SupportsBytes, Tuple, Type, Union

from semver import Version

from ethereum_test_forks import Fork

from ..common.conversions import to_bytes
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
    return fork.solc_name()


class Yul(SupportsBytes, Sized):
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

    def __bytes__(self) -> bytes:
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

    def __len__(self) -> int:
        """
        Get the length of the Yul bytecode.
        """
        return len(bytes(self))

    def __add__(self, other: str | bytes | SupportsBytes) -> Code:
        """
        Adds two code objects together, by converting both to bytes first.
        """
        return Code(bytes(self) + to_bytes(other))

    def __radd__(self, other: str | bytes | SupportsBytes) -> Code:
        """
        Adds two code objects together, by converting both to bytes first.
        """
        return Code(to_bytes(other) + bytes(self))

    def version(self) -> Version:
        """
        Return solc's version string
        """
        result = run(
            [self.binary, "--version"],
            stdout=PIPE,
            stderr=PIPE,
        )
        solc_output = result.stdout.decode().split("\n")
        version_pattern = r"Version: (.*)"
        solc_version_string = ""
        for line in solc_output:
            if match := re.search(version_pattern, line):
                solc_version_string = match.group(1)
                break
        if not solc_version_string:
            warnings.warn("Unable to determine solc version.")
            return Version(0)
        # Sanitize
        solc_version_string = solc_version_string.replace("g++", "gpp")
        return Version.parse(solc_version_string)


YulCompiler = Type[Yul]
