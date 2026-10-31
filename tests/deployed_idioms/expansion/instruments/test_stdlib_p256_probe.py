"""
THROWAWAY MEASUREMENT INSTRUMENT -- its failures are the measurement.

Two things to measure before anything is pinned:

1. a widely used P256 library presence probe, reproduced verbatim in
   EVM bytecode with that library's own wycheproof vector. Does EELS's `p256verify`
   accept it (returning 32 bytes of 1) from Osaka, and does the call to the
   unassigned address return success-with-empty-returndata before Osaka?

2. Whether any code-inspection idiom can tell a precompile from an empty
   account: `EXTCODESIZE`, `EXTCODEHASH`, `BALANCE`.

Packs observables into one word and asserts a sentinel.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0xDEAD

# a widely used contract library `utils/cryptography/P256.sol::_tryVerifyNative`
# presence probe: "a valid signature with small r and s values", taken from
# C2SP/wycheproof ecdsa_secp256r1_sha256_p1363_test.json#L1173-L1204.
LIB_H = 0xBB5A52F42F9C9261ED4361F59422A1E30036E7C32B270C8807A419FECA605023
LIB_R = 0x0000000000000000000000000000000000000000000000000000000000000005
LIB_S = 0x0000000000000000000000000000000000000000000000000000000000000001
LIB_QX = 0xA71AF64DE5126A4A4E02B7922D66CE9415CE88A4C9D25514D91082C8725AC957
LIB_QY = 0x5D47723C8FBE580BB369FEC9C2665D8E30A435B9932645482E7C9F11E872296B

P256VERIFY = 0x100


@pytest.mark.valid_from("Berlin")
def test_probe_lib_rip7212(state_test: StateTestFiller, pre: Alloc) -> None:
    """isValid << 16 | RETURNDATASIZE << 8 | success."""
    probe = pre.deploy_contract(
        Op.MSTORE(0x100, LIB_H)
        + Op.MSTORE(0x120, LIB_R)
        + Op.MSTORE(0x140, LIB_S)
        + Op.MSTORE(0x160, LIB_QX)
        + Op.MSTORE(0x180, LIB_QY)
        # that library: zero the scratch word so an empty return reads as false.
        + Op.MSTORE(0x00, 0)
        + Op.MSTORE(
            0x200,
            Op.STATICCALL(
                gas=Op.GAS,
                address=Address(P256VERIFY),
                args_offset=0x100,
                args_size=0xA0,
                ret_offset=0x00,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(
            0,
            Op.ADD(
                Op.ADD(
                    Op.SHL(16, Op.MLOAD(0x00)),
                    Op.SHL(8, Op.RETURNDATASIZE),
                ),
                Op.MLOAD(0x200),
            ),
        )
        + Op.STOP
    )
    tx = Transaction(to=probe, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={probe: Account(storage={0: SENTINEL})}, tx=tx)


@pytest.mark.parametrize(
    "addr",
    [
        pytest.param(0x05, id="modexp_always_a_precompile"),
        pytest.param(0x100, id="p256verify_from_osaka"),
        pytest.param(0x12, id="never_assigned"),
    ],
)
@pytest.mark.valid_from("Berlin")
def test_probe_code_inspection(
    state_test: StateTestFiller, pre: Alloc, addr: int
) -> None:
    """EXTCODESIZE << 128 | BALANCE << 64 | ISZERO(EXTCODEHASH)."""
    probe = pre.deploy_contract(
        Op.SSTORE(
            0,
            Op.ADD(
                Op.ADD(
                    Op.SHL(128, Op.EXTCODESIZE(Address(addr))),
                    Op.SHL(64, Op.BALANCE(Address(addr))),
                ),
                Op.ISZERO(Op.EXTCODEHASH(Address(addr))),
            ),
        )
        + Op.STOP
    )
    tx = Transaction(to=probe, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={probe: Account(storage={0: SENTINEL})}, tx=tx)
