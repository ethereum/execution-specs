"""compile yul with arguments."""

import subprocess


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
    cmd = ["solc"]
    if evm_version:
        cmd.extend(["--evm-version", evm_version])

    # Choose flags based on whether flag is provided
    if optimize is None:
        # When flag is not provided, include extra optimization flags
        cmd.extend(["--strict-assembly", "--optimize", "--yul-optimizations=:", source_file])
    else:
        # Otherwise, omit the optimization flags
        cmd.extend(["--strict-assembly", source_file])

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
