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
                stderr_lines = result.stderr.decode().split("\n")
                stderr_message = "\n".join(
                    line.strip() for line in stderr_lines
                )
                raise Exception(
                    f"failed to compile yul source:\n{stderr_message[7:]}"
                )

            lines = result.stdout.decode().split("\n")

            hex_str = lines[lines.index("Binary representation:") + 1]

            self.compiled = bytes.fromhex(hex_str)
        return self.compiled
