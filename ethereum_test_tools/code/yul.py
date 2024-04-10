"""
Yul frontend
"""

import re
import warnings
from functools import cached_property
from pathlib import Path
from shutil import which
from subprocess import CompletedProcess, run
from typing import Optional, Sized, SupportsBytes, Type

from semver import Version

from ethereum_test_forks import Fork

from ..common.conversions import to_bytes
from .code import Code

DEFAULT_SOLC_ARGS = ("--assemble", "-")
VERSION_PATTERN = re.compile(r"Version: (.*)")


class Solc:
    """Solc compiler."""

    binary: Path

    def __init__(
        self,
        binary: Optional[Path | str] = None,
    ):
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

    def run(self, *args: str, input: str | None = None) -> CompletedProcess:
        """Run solc with the given arguments"""
        return run(
            [self.binary, *args],
            capture_output=True,
            text=True,
            input=input,
        )

    @cached_property
    def version(self) -> Version:
        """Return solc's version"""
        for line in self.run("--version").stdout.splitlines():
            if match := VERSION_PATTERN.search(line):
                # Sanitize
                solc_version_string = match.group(1).replace("g++", "gpp")
                return Version.parse(solc_version_string)
        warnings.warn("Unable to determine solc version.")
        return Version(0)


class Yul(Solc, SupportsBytes, Sized):
    """
    Yul compiler.
    Compiles Yul source code into bytecode.
    """

    source: str
    evm_version: str | None

    def __init__(
        self,
        source: str,
        fork: Optional[Fork] = None,
        binary: Optional[Path | str] = None,
    ):
        super().__init__(binary)
        self.source = source
        self.evm_version = fork.solc_name() if fork else None

    @cached_property
    def compiled(self) -> bytes:
        """Returns the compiled Yul source code."""
        solc_args = ("--evm-version", self.evm_version) if self.evm_version else ()

        result = self.run(*solc_args, *DEFAULT_SOLC_ARGS, input=self.source)

        if result.returncode:
            stderr_lines = result.stderr.splitlines()
            stderr_message = "\n".join(line.strip() for line in stderr_lines)
            raise Exception(f"failed to compile yul source:\n{stderr_message[7:]}")

        lines = result.stdout.splitlines()

        hex_str = lines[lines.index("Binary representation:") + 1]

        return bytes.fromhex(hex_str)

    def __bytes__(self) -> bytes:
        """
        Assembles using `solc --assemble`.
        """
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


YulCompiler = Type[Yul]
