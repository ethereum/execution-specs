"""
Yul frontend
"""

from pathlib import Path
from subprocess import PIPE, run
from typing import Optional

from .code import Code

SOLC: Path = Path("solc")
SOLC_ARGS = (
    SOLC,
    "--assemble",
    "-",
)


class Yul(Code):
    """
    Yul compiler.
    Compiles Yul source code into bytecode.
    """

    source: str
    compiled: Optional[bytes] = None

    def __init__(self, source: str):
        self.source = source

    def assemble(self) -> bytes:
        """
        Assembles using `solc --assemble`.
        """
        if not self.compiled:

            result = run(
                SOLC_ARGS,
                input=str.encode(self.source),
                stdout=PIPE,
                stderr=PIPE,
            )

            if result.returncode != 0:
                raise Exception("failed to compile yul source")

            lines = result.stdout.decode().split("\n")

            hex_str = lines[lines.index("Binary representation:") + 1]

            self.compiled = bytes.fromhex(hex_str)
        return self.compiled
