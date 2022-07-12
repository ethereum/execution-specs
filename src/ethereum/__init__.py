"""
Ethereum Specification
^^^^^^^^^^^^^^^^^^^^^^
Seeing as internet connections have been vastly expanding across the
world, spreading information has become as cheap as ever. Bitcoin, for
example, has demonstrated the possibility of creating a decentralized,
trade system that is accessible around the world. Namecoin is another
system that built off of Bitcoin's currency structure to create other
simple technological applications.

Ethereum's goal is to create a cryptographically secure system in which
any and all types of transaction-based concepts can be built. It provides
an exceptionally accessible and decentralized system to build software
and execute transactions.

This package contains a reference implementation, written as simply as
possible, to aid in defining the behavior of Ethereum clients.
"""
import sys
from typing import Any

import cffi

__version__ = "0.1.0"

try:
    # These incantations are necessary to make ripemd160 work on OpenSSL 3
    ffi = cffi.FFI()
    ffi.cdef("void *OSSL_PROVIDER_load(void *libctx, const char *name);")
    lib = ffi.dlopen("crypto")
    assert (
        lib.OSSL_PROVIDER_load(
            ffi.NULL, ffi.new("char[]", "default".encode("ascii"))
        )
        is not ffi.NULL
    )
    assert (
        lib.OSSL_PROVIDER_load(
            ffi.NULL, ffi.new("char[]", "legacy".encode("ascii"))
        )
        is not ffi.NULL
    )
except Exception:
    # Ignore all failures, the code above is fragile and will fail in
    # situations when it is not needed (e.g. you don't have OpenSSL 3).
    pass

#
#  Ensure we can reach 1024 frames of recursion
#
EVM_RECURSION_LIMIT = 1024 * 12
sys.setrecursionlimit(max(EVM_RECURSION_LIMIT, sys.getrecursionlimit()))


def evm_trace(evm: Any, op: Any) -> None:
    """
    Placeholder for an evm trace function. The spec does not trace evm by
    default. EVM tracing will be injected if the user requests it.
    """
    pass
