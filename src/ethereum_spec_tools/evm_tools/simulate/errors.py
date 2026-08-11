"""
Map spec exceptions onto `eth_simulateV1` error codes.

`eth_simulateV1` does not report an inadmissible call as a failed entry
in the `calls` array — it abandons the whole request and returns a
JSON-RPC error. Most of those codes name a condition the specification
already raises an exception for, so the mapping is mechanical. The
message is not: execution-apis says outright that "the error messages
are suggestions", so only the code is assertable, which is the same
position hive's `rpc-compat` reached when it started stripping
`error.message` before comparing.
"""

from typing import Dict, Optional

REVERT_ERROR_CODE = 3
"""`execution reverted`, reported per call rather than for the request."""

VM_ERROR_CODE = -32015
"""A non-revert halt, reported per call rather than for the request."""


class SimulateError(Exception):
    """A condition that abandons the whole `eth_simulateV1` request."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


SPEC_EXCEPTION_CODES: Dict[str, int] = {
    "NonceMismatchError:nonce too low": -38010,
    "NonceMismatchError:nonce too high": -38011,
    "InsufficientMaxFeePerGasError": -38012,
    "InsufficientTransactionGasError": -38013,
    "InsufficientBalanceError": -38014,
    "GasUsedExceedsLimitError": -38015,
    "InvalidSenderError": -38024,
    "InitCodeTooLargeError": -38025,
}
"""
Spec exception names, and the code the request fails with.

Eight of the method's twenty-six codes are reachable this way. The
remainder are either transport-level (`-32602`, `-32603`, `-32000`),
resource limits a client chooses for itself (`-32016` timeout, `-38026`
"client adjustable limit exceeded"), or ordering and override rules
that belong to the request rather than to execution (`-38020` …
`-38023`), which this module's caller raises directly.
"""


def error_code_for(exception: BaseException) -> Optional[int]:
    """
    Return the `eth_simulateV1` code for a spec exception, if there is
    one.

    The nonce cases are distinguished by message because the spec raises
    one exception type for both directions, while the method assigns
    them different codes.
    """
    name = type(exception).__name__
    if name == "NonceMismatchError":
        text = str(exception)
        if "too low" in text:
            return SPEC_EXCEPTION_CODES["NonceMismatchError:nonce too low"]
        if "too high" in text:
            return SPEC_EXCEPTION_CODES["NonceMismatchError:nonce too high"]
        return None
    return SPEC_EXCEPTION_CODES.get(name)


__all__ = [
    "REVERT_ERROR_CODE",
    "SPEC_EXCEPTION_CODES",
    "SimulateError",
    "VM_ERROR_CODE",
    "error_code_for",
]
