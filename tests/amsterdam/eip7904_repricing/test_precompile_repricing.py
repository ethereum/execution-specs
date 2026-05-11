"""
Test EIP-7904 precompile gas repricing.

For each repriced precompile, verify that a call provided exactly the new gas
cost succeeds, and a call provided one gas less fails (CALL returns 0).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import Spec, ref_spec_7904

REFERENCE_SPEC_GIT_PATH = ref_spec_7904.git_path
REFERENCE_SPEC_VERSION = ref_spec_7904.version

pytestmark = [pytest.mark.valid_from("Amsterdam")]


# --- Test vectors ---

# ECADD: identity + identity = identity. 128-byte zero input is valid.
ECADD_INPUT = b"\x00" * 128

# BLAKE2F: RFC-7693 / EIP-152 reference vector for "abc" (12 rounds).
BLAKE2F_ROUNDS = 12
BLAKE2F_INPUT = (
    BLAKE2F_ROUNDS.to_bytes(4, "big")
    + bytes.fromhex(
        "48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1"
        "361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f"
        "79217e1319cde05b"
    )
    + bytes.fromhex(
        "616263000000000000000000000000000000000"
        "00000000000000000000000000000000000000000000000000000000000000000"
        "00000000000000000000000000000000000000000000000000000000000000000"
        "00000000000000000000000000000000000000000000000000000000000000000"
        "0000000000000000000000"
    )
    + (3).to_bytes(8, "little")
    + (0).to_bytes(8, "little")
    + b"\x01"  # f = true
)
assert len(BLAKE2F_INPUT) == 213

# P256VERIFY: valid Wycheproof signature (taken from EIP-7951 test vectors).
P256VERIFY_INPUT = bytes.fromhex(
    "bb5a52f42f9c9261ed4361f59422a1e30036e7c32b270c8807a419feca605023"
    "2ba3a8be6b94d5ec80a6d9d1190a436effe50d85a1eee859b8cc6af9bd5c2e18"
    "4cd60b855d442f5b3c7b11eb6c4e0ae7525fe710fab9aa7c77a67f79e6fadd76"
    "2927b10512bae3eddcfe467828128bad2903269919f7086069c8c4df6c732838"
    "c7787964eaac00e5921fb1498a60f4606766b3d9685001558d1a974e7341513e"
)
assert len(P256VERIFY_INPUT) == 160


# (address, input, base_gas)
CASES = [
    pytest.param(
        Spec.ECADD_ADDRESS,
        ECADD_INPUT,
        Spec.PRECOMPILE_ECADD,
        id="ecadd",
    ),
    pytest.param(
        Spec.BLAKE2F_ADDRESS,
        BLAKE2F_INPUT,
        Spec.PRECOMPILE_BLAKE2F_BASE
        + BLAKE2F_ROUNDS * Spec.PRECOMPILE_BLAKE2F_PER_ROUND,
        id="blake2f",
    ),
    pytest.param(
        Spec.P256VERIFY_ADDRESS,
        P256VERIFY_INPUT,
        Spec.PRECOMPILE_P256VERIFY,
        id="p256verify",
    ),
]


@pytest.mark.parametrize("precompile_address,input_data,precompile_gas", CASES)
@pytest.mark.parametrize(
    "gas_delta,expected_call_result",
    [
        pytest.param(0, 1, id="exact_gas"),
        pytest.param(-1, 0, id="one_gas_short"),
    ],
)
def test_precompile_gas_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    precompile_address: int,
    input_data: bytes,
    precompile_gas: int,
    gas_delta: int,
    expected_call_result: int,
) -> None:
    """
    Call the precompile with `precompile_gas + gas_delta`. With the exact new
    gas (gas_delta=0) the CALL succeeds; with one gas less the precompile
    runs out of gas and CALL returns 0.
    """
    caller_input_offset = 0
    code = (
        # Copy calldata into memory so we can hand it to the precompile.
        Op.CALLDATACOPY(caller_input_offset, 0, Op.CALLDATASIZE())
        + Op.SSTORE(
            0,
            Op.CALL(
                precompile_gas + gas_delta,
                precompile_address,
                0,
                caller_input_offset,
                Op.CALLDATASIZE(),
                0,
                0,
            ),
        )
        + Op.STOP
    )
    caller = pre.deploy_contract(code=code)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        data=input_data,
        gas_limit=1_000_000,
    )

    post = {caller: Account(storage={0: expected_call_result})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# POINT_EVALUATION is exercised separately because its valid input requires a
# correct KZG proof. Reuse the canonical "INF point" vector that the EIP-4844
# tests use: commitment and proof are the BLS12-381 G1 identity element, which
# the precompile accepts for any (z, y=0) pair.
_INF_POINT = (0xC0 << 376).to_bytes(48, byteorder="big")
_Z = (
    0x623CE31CF9759A5C8DAF3A357992F9F3DD7F9339D8998BC8E68373E54F00B75E
).to_bytes(32, byteorder="big")


def _versioned_hash(commitment: bytes) -> bytes:
    from hashlib import sha256

    return b"\x01" + sha256(commitment).digest()[1:]


POINT_EVALUATION_INPUT = (
    _versioned_hash(_INF_POINT)
    + _Z
    + (0).to_bytes(32, "big")
    + _INF_POINT
    + _INF_POINT
)
assert len(POINT_EVALUATION_INPUT) == 192


@pytest.mark.parametrize(
    "gas_delta,expected_call_result",
    [
        pytest.param(0, 1, id="exact_gas"),
        pytest.param(-1, 0, id="one_gas_short"),
    ],
)
def test_point_evaluation_gas_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    gas_delta: int,
    expected_call_result: int,
) -> None:
    """
    Verify the EIP-7904 point evaluation cost is enforced at the gas
    boundary.
    """
    code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
        + Op.SSTORE(
            0,
            Op.CALL(
                Spec.PRECOMPILE_POINT_EVALUATION + gas_delta,
                Spec.POINT_EVALUATION_ADDRESS,
                0,
                0,
                Op.CALLDATASIZE(),
                0,
                0,
            ),
        )
        + Op.STOP
    )
    caller = pre.deploy_contract(code=code)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        data=POINT_EVALUATION_INPUT,
        gas_limit=1_000_000,
    )

    post = {caller: Account(storage={0: expected_call_result})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)
