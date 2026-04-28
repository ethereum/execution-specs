# Exception Tests

## Overview

Exception tests validate that clients correctly reject invalid blocks and transactions with appropriate error messages. The Engine simulator provides advanced exception verification using client-specific mappers to handle varying error message formats across different clients.

## How Exception Testing Works

1. **Test fixtures specify expected exceptions** - Each test defines what error should occur
2. **Clients reject invalid payloads** - Via Engine API or block import
3. **Exception mappers translate errors** - Client-specific error messages are normalized
4. **Test framework validates** - Ensures the correct exception type was raised

## Client Exception Mappers

Each client has unique error message formats. EEST maintains exception mappers that translate client-specific errors to standardized exception types.

### Mapper Location

Exception mappers are defined in the EEST codebase:

- `packages/testing/src/execution_testing/client_clis/clis/<client>.py` (e.g., `geth.py`, `besu.py`, `nethermind.py`)

### Example Mapper Structure

```python
# Simplified example
GETH_EXCEPTIONS = {
    "invalid block: gas limit reached": ExceptionType.GAS_LIMIT_EXCEEDED,
    "block gas cost exceeds gas limit": ExceptionType.GAS_LIMIT_EXCEEDED,
    "insufficient balance for transfer": ExceptionType.INSUFFICIENT_BALANCE,
}
```

## External Client Exception Mappers

Client repositories can extend EEST's built-in exception mappers with a
client-owned YAML file. External mappings are additive: they do not remove or
replace mappings maintained in EEST.

```yaml
version: 1
name: geth-ci
substring:
  TransactionException.INSUFFICIENT_ACCOUNT_FUNDS:
    - "insufficient funds for gas * price + value"
regex:
  BlockException.INVALID_GASLIMIT:
    - 'child gas_limit \d+ .*'
```

Rules:

- `version` must be `1`.
- Exception keys must be exact EEST names such as
  `TransactionException.INSUFFICIENT_ACCOUNT_FUNDS` or
  `BlockException.INVALID_GASLIMIT`.
- `substring` and `regex` values can be a string or a list of strings.
- Empty patterns, unknown exception names, unknown top-level sections, and
  invalid regular expressions are rejected when the file is loaded.

For `validate`, add the mapper path to the relevant client section in
`validate.toml`. Relative paths are resolved from the directory containing
`validate.toml`.

```toml
[geth]
bin = "../go-ethereum/build/bin/evm"
exception-mapper = "../go-ethereum/eest-exceptions.yaml"
```

For Hive-backed `consume` commands, pass one or more mapper files on the
command line:

```bash
uv run consume engine \
  --input ./fixtures \
  --exception-mapper geth=../go-ethereum/eest-exceptions.yaml
```

The `CLIENT` key is matched against Hive client names. For example, `geth`
extends the mapper selected for `go-ethereum`.

## Updating Built-In Client Exception Messages

When clients change their error messages or you encounter unmapped exceptions:

### 1. Identify the Unmapped Exception

Run the test and observe the actual error message:

```bash
uv run consume engine -k "test_invalid_gas_limit" -v
```

Look for output like:

```text
Unmapped exception from client 'go-ethereum': "block gas cost exceeds limit: have 30000001, limit 30000000"
```

### 2. Update the Exception Mapper

Edit the client's exception mapper in `packages/testing/src/execution_testing/client_clis/clis/<client>.py`:

```python
# In packages/testing/src/execution_testing/client_clis/clis/geth.py
class GethCLI(TransitionTool):
    exception_map = {
        # Existing mappings...
        "block gas cost exceeds limit": ExceptionType.GAS_LIMIT_EXCEEDED,  # New mapping
    }
```

### 3. Test the Update

Re-run the test to verify the exception is now properly mapped:

```bash
uv run consume engine -k "test_invalid_gas_limit" --disable-strict-exception-matching=false
```

### 4. Submit Changes

Create a pull request with:

- Updated exception mappings
- Test results showing the fix
- Any relevant client version information

## Disabling Strict Exception Matching

For development or when exception mappings are incomplete:

```bash
# Disable for specific clients
uv run consume engine --disable-strict-exception-matching=nimbus-el
```

!!! warning "Production Testing"
    Always enable strict exception matching for production test runs to ensure clients properly validate consensus rules.

## Debugging Exception Test Failures

### Check Client Logs

Enable verbose client output:

```bash
./hive --sim ethereum/eels/consume-engine \
  --docker.output \
  --sim.loglevel 5
```

### Verify Exception Type

Ensure the test expects the correct exception:

```python
# In test file
post = {
    address: Account(
        balance=0,
        storage={},
        exception=TransactionException.INSUFFICIENT_BALANCE  # Expected exception
    )
}
```

### Test Without Exceptions

Temporarily modify the test to see what happens without the invalid condition:

```bash
# Run specific test in isolation
uv run consume engine -k "test_name_without_invalid"
```

## Contributing Exception Mappings

When contributing new exception mappings:

1. **Document the client version** - Exception messages may change between versions
2. **Use regex patterns** - For flexible matching: `r"gas limit.*exceeded"`
3. **Test multiple scenarios** - Ensure the pattern doesn't over-match
4. **Add comments** - Explain non-obvious mappings

Example contribution:

```python
# Besu v24.1.0+ changed gas limit error format
BESU_EXCEPTIONS = {
    # Old format (pre-24.1.0)
    "Transaction gas limit exceeds block gas limit": ExceptionType.GAS_LIMIT_EXCEEDED,
    # New format (24.1.0+)
    r"block gas limit \(\d+\) exceeded by transaction": ExceptionType.GAS_LIMIT_EXCEEDED,
}
```
