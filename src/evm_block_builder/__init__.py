"""
Python wrapper for the `evm b11r` tool.
"""

import json
import subprocess
from abc import abstractmethod
from pathlib import Path
from shutil import which
from typing import Any, Optional, Tuple


class BlockBuilder:
    """
    Generic Block builder frontend.
    """

    @abstractmethod
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
        Build a block with specified parameters and return RLP and hash
        """
        pass

    @abstractmethod
    def version(self) -> str:
        """
        Return name and version of tool used to build the block
        """
        pass


class EvmBlockBuilder(BlockBuilder):
    """
    Go-ethereum `evm` Block builder frontend.
    """

    binary: Path
    cached_version: Optional[str] = None

    def __init__(self, binary: Optional[Path] = None):
        if binary is None:
            which_path = which("evm")
            if which_path is not None:
                binary = Path(which_path)
        if binary is None or not binary.exists():
            raise Exception(
                """`evm` binary executable is not accessible, please refer to
                https://github.com/ethereum/go-ethereum on how to compile and
                install the full suite of utilities including the `evm` tool"""
            )
        self.binary = binary

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

        result = subprocess.run(
            args,
            input=str.encode(json.dumps(stdin)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if result.returncode != 0:
            raise Exception("failed to build")

        output = json.loads(result.stdout)

        if "rlp" not in output or "hash" not in output:
            Exception("malformed result")

        return (output["rlp"], output["hash"])

    def version(self) -> str:
        """
        Gets `evm` binary version.
        """
        if self.cached_version is None:

            result = subprocess.run(
                [str(self.binary), "-v"],
                stdout=subprocess.PIPE,
            )

            if result.returncode != 0:
                raise Exception(
                    "failed to evaluate: " + result.stderr.decode()
                )

            self.cached_version = result.stdout.decode().strip()

        return self.cached_version
