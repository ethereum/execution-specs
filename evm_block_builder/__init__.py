"""
Python wrapper for the `evm b11r` tool.
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Optional, Tuple

from ethereum.crypto import Hash32
from ethereum.utils.hexadecimal import hex_to_hash


class BlockBuilder:
    """
    Block builder frontend.
    """

    binary: Path = Path("evm")

    def build(
        self,
        header: Any,
        txs: Any,
        ommers: Any,
        clique: Optional[Any] = None,
        ethash: bool = False,
        ethashMode: str = "normal",
    ) -> Tuple[str, str]:
        """
        Executes `evm b11r` with the specified arguments.
        """
        args = [
            str(self.binary),
            "b11r",
            "--input.header=stdin",
            "--input.txs=stdin",
            "--input.ommers=stdin",
            "--seal.clique=stdin",
            "--output.block=stdout",
        ]

        if ethash:
            args.append("--seal.ethash")
            args.append("--seal.ethash.mode=" + ethashMode)

        stdin = {
            "header": header,
            "txs": txs,
            "uncles": ommers,
            "clique": clique,
        }
        print(str.encode(json.dumps(stdin)))
        result = subprocess.run(
            args, input=str.encode(json.dumps(stdin)), stdout=subprocess.PIPE
        )

        if result.returncode != 0:
            raise Exception("Failed to evaluate: " + str(result.stderr))

        output = json.loads(result.stdout)

        if "rlp" not in output or "hash" not in output:
            Exception("Malformed result")

        return (output["rlp"], output["hash"])
