# Installation Troubleshooting

This page provides guidance on how to troubleshoot common issues that may arise when installing [ethereum/execution-spec-tests](https://github.com/ethereum/execution-spec-tests).

## Problem: `Failed building wheel for coincurve`

!!! danger "Problem: `Failed building wheel for coincurve`"
    Installing EEST and its dependencies via `uv sync --all-extras` fails with:

    ```bash
    Stored in directory: /tmp/...
      Building wheel for coincurve (pyproject.toml) ... error
      error: subprocess-exited-with-error
      
      × Building wheel for coincurve (pyproject.toml) did not run successfully.
      │ exit code: 1
      ╰─> [27 lines of output]
          ...
            571 | #include <secp256k1_extrakeys.h>
                |          ^~~~~~~~~~~~~~~~~~~~~~~
          compilation terminated.
          error: command '/usr/bin/gcc' failed with exit code 1
          [end of output]
      
      note: This error originates from a subprocess, and is likely not a problem with pip.
      ERROR: Failed building wheel for coincurve
    ```

!!! success "Solution: Install the `libsecp256k1` library"
    On Ubuntu, you can install this library with:

    ```bash
    sudo apt update
    sudo apt-get install libsecp256k1-dev
    ```

## Problem: `solc` Installation issues

### Problem: `CERTIFICATE_VERIFY_FAILED`

!!! danger "Problem: `Failed to ... CERTIFICATE_VERIFY_FAILED`"
    When running `fill` you might encounter the following error:

    ```bash
    Exit: Failed to ...: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:992)>
    ```

=== "Ubuntu"

    !!! success "Solution: Update your system’s CA certificates"
        On Ubuntu, run the following commands:

        ```bash
        sudo apt-get update
        sudo apt-get install ca-certificates
        ```

=== "macOS"

    !!! success "Solution: Update your system’s CA certificates"
        On macOS, Python provides a built-in script to install the required certificates:

        ```bash
        /Applications/Python\ 3.11/Install\ Certificates.command
        ```

### Problem: `Exception: failed to compile yul source`

!!! danger "Problem: `Running fill on static_tests fails with tests that contain yul source code` on ARM platforms"
    To resolve the issue you must acquire the `solc` binary e.g. by building solidity from source. The guide below installs v0.8.28 but you might prefer to choose a different version.

!!! success "Solution: Build solc from source"
    The following steps have been tested on Ubuntu 24.04.2 LTS ARM64:
    ```bash
    git clone --branch v0.8.28 --depth 1 https://github.com/ethereum/solidity.git
    cd solidity && mkdir build && cd build
    sudo apt install build-essential libboost-all-dev z3
    cmake ..
    make
    mv $HOME/Documents/execution-spec-tests/.venv/bin/solc $HOME/Documents/execution-spec-tests/.venv/bin/solc-x86-64
    cp ./solc/solc $HOME/Documents/execution-spec-tests/.venv/bin/
    chmod +x $HOME/Documents/execution-spec-tests/.venv/bin/solc
    ```
    Running `uv run solc --version` should now return the expected version.

## Problem: `ValueError: unsupported hash type ripemd160`

!!! danger "Problem: `Running fill fails with tests that use the RIPEMD160 precompile (0x03)`"
    When running `fill`, you encounter the following error:

    ```python
    ValueError: unsupported hash type ripemd160
    # or
    ValueError: [digital envelope routines] unsupported
    ```

    This is due to the removal of certain cryptographic primitives in OpenSSL 3. These were re-introduced in [OpenSSL v3.0.7](https://github.com/openssl/openssl/blob/master/CHANGES.md#changes-between-306-and-307-1-nov-2022).

!!! success "Solution: Modify OpenSSL configuration"
    On platforms where OpenSSL v3.0.7 is unavailable (e.g., Ubuntu 22.04), modify your OpenSSL configuration to enable RIPEMD160. Make the following changes in the OpenSSL config file:

    ```ini
    [openssl_init]
    providers = provider_sect
    
    # List of providers to load
    [provider_sect]
    default = default_sect
    legacy = legacy_sect

    [default_sect]
    activate = 1

    [legacy_sect]
    activate = 1
    ```

    This will enable the legacy cryptographic algorithms, including RIPEMD160. See [ethereum/execution-specs#506](https://github.com/ethereum/execution-specs/issues/506) for more information.

## Problem: VS Code "Autoformat on Save" with Ruff Not Working

!!! danger "Problem: 'Autoformat on Save' with Ruff not working as expected in VS Code"
    If you are using VS Code and "autoformat on save" is not working as expected, or if it produces different formatting than the official `tox -e lint` command, you may have a version mismatch with the `ruff` formatter. This problem can be confirmed if `git diff` shows changes to an otherwise unmodified file after you have saved it.

    This issue often occurs when VS Code is not configured to use the project's virtual environment (`.venv`) or if the linting dependencies have not been installed. In this case, VS Code's Ruff extension falls back to a bundled version of `ruff`, which may not match the version pinned in the project's `pyproject.toml` file.

!!! success "Solution: Install all required dependencies and select the correct interpreter"

    1.  Ensure all dependencies are installed, including the `lint` extras.

        ```bash
        uv sync --all-extras
        ```

    2.  In VS Code, open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`) and select `Python: Select Interpreter`.
    
    3.  Choose the interpreter located in the project's `.venv` directory. This ensures VS Code uses the correct `ruff` version from your project's environment.
    
## Other Issues Not Listed?

If you're facing an issue that's not listed here, you can easily report it on GitHub for resolution.

[Click here to report a documentation issue related to installation](https://github.com/ethereum/execution-spec-tests/issues/new?title=docs(bug):%20unable%20to%20install%20eest%20with%20error%20...&labels=scope:docs,type:bug&body=%3Ccopy-paste%20command%20that%20triggered%20the%20issue%20here%3E%0A%3Ccopy-paste%20output%20or%20attach%20screenshot%20here%3E)

Please include the following details in your report:

1. The command that triggered the issue.
2. Any relevant error messages or screenshots.
3. Relevant version information from the output of `uv run eest info` (if running consume from within `eest`).
