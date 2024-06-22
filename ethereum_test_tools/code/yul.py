"""
Yul frontend
"""

import re
import warnings
from functools import cached_property
from pathlib import Path
from shutil import which
from subprocess import CompletedProcess, run
from typing import Optional, Type

from semver import Version

from ethereum_test_forks import Fork
from ethereum_test_vm import Bytecode

DEFAULT_SOLC_ARGS = ("--assemble", "-")
VERSION_PATTERN = re.compile(r"Version: (.*)")


class Solc:
    """Solc compiler."""

    binary: Path

    def __init__(
        self,
        binary: Optional[Path | str] = None,
    ):
        if not binary:
            which_path = which("solc")
            if which_path is not None:
                binary = Path(which_path)
        if not binary or not Path(binary).exists():
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


class Yul(Bytecode):
    """
    Yul compiler.
    Compiles Yul source code into bytecode.
    """

    source: str
    evm_version: str | None

    def __new__(
        cls,
        source: str,
        fork: Optional[Fork] = None,
        binary: Optional[Path | str] = None,
    ):
        """
        Compile Yul source code into bytecode.
        """
        solc = Solc(binary)
        evm_version = fork.solc_name() if fork else None

        solc_args = ("--evm-version", evm_version) if evm_version else ()

        result = solc.run(*solc_args, *DEFAULT_SOLC_ARGS, input=source)

        if result.returncode:
            stderr_lines = result.stderr.splitlines()
            stderr_message = "\n".join(line.strip() for line in stderr_lines)
            raise Exception(f"failed to compile yul source:\n{stderr_message[7:]}")

        lines = result.stdout.splitlines()

        hex_str = lines[lines.index("Binary representation:") + 1]

        bytecode = bytes.fromhex(hex_str)
        instance = super().__new__(
            cls,
            bytecode,
            popped_stack_items=0,
            pushed_stack_items=0,
        )
        instance.source = source
        instance.evm_version = evm_version
        return instance


YulCompiler = Type[Yul]
