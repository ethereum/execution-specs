"""compile yul with arguments."""

import subprocess
from pathlib import Path
from typing import LiteralString


def safe_solc_command(
    source_file: Path | str, evm_version: str | None = None, optimize: str | None = None
) -> list[str]:
    """Safely construct solc command with validated inputs."""
    # Validate source file path
    source_path = Path(source_file)
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_file}")
    if source_path.suffix not in (".yul", ".sol"):
        raise ValueError(f"Invalid file extension for solc: {source_path.suffix}")

    cmd: list[str] = ["solc"]

    # Add EVM version if provided (validate against known versions)
    if evm_version:
        valid_versions = {
            "homestead",
            "tangerineWhistle",
            "spuriousDragon",
            "byzantium",
            "constantinople",
            "petersburg",
            "istanbul",
            "berlin",
            "london",
            "paris",
            "shanghai",
            "cancun",
        }
        if evm_version not in valid_versions:
            raise ValueError(f"Invalid EVM version: {evm_version}")
        cmd.extend(["--evm-version", evm_version])

    # Add compilation flags (using literal strings)
    strict_assembly: LiteralString = "--strict-assembly"
    cmd.append(strict_assembly)

    if optimize is None:
        optimize_flag: LiteralString = "--optimize"
        yul_opts: LiteralString = "--yul-optimizations=:"
        cmd.extend([optimize_flag, yul_opts])

    cmd.append(str(source_path))
    return cmd


def compile_yul(source_file: str, evm_version: str | None = None, optimize: str | None = None):
    """
    Compiles a Yul source file using solc and returns the binary representation.

    Parameters_:
        source_file (str): Path to the Yul source file.
        evm_version (str, optional): The EVM version to use (e.g., 'istanbul'). Defaults to None.
        optimize (any, optional): If provided (non-None), optimization flags are not added.
                              If None, additional optimization flags will be included.

    Returns_:
        str: The binary representation prefixed with "0x".

    Raises_:
        Exception: If the solc output contains an error message.
    """
    cmd = safe_solc_command(source_file, evm_version, optimize)

    # Execute the solc command and capture both stdout and stderr
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False
    )
    out = result.stdout

    # Check for errors in the output
    if "Error" in out:
        raise Exception(f"Yul compilation error:\n{out}")

    # Search for the "Binary representation:" line and get the following line as the binary
    lines = out.splitlines()
    binary_line = ""
    for i, line in enumerate(lines):
        if "Binary representation:" in line:
            if i + 1 < len(lines):
                binary_line = lines[i + 1].strip()
            break

    return f"0x{binary_line}"
