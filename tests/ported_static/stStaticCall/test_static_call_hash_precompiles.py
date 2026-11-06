"""
STATICCALL the IDENTITY, SHA256 and RIPEMD160 precompiles.

Ported from:
state_tests/stStaticCall/static_CallIdentitiy_1Filler.json
state_tests/stStaticCall/static_CallIdentity_1_nonzeroValueFiller.json
state_tests/stStaticCall/static_CallIdentity_2Filler.json
state_tests/stStaticCall/static_CallIdentity_3Filler.json
state_tests/stStaticCall/static_CallIdentity_4Filler.json
state_tests/stStaticCall/static_CallIdentity_4_gas17Filler.json
state_tests/stStaticCall/static_CallIdentity_4_gas18Filler.json
state_tests/stStaticCall/static_CallIdentity_5Filler.json
state_tests/stStaticCall/static_CallRipemd160_1Filler.json
state_tests/stStaticCall/static_CallRipemd160_2Filler.json
state_tests/stStaticCall/static_CallRipemd160_3Filler.json
state_tests/stStaticCall/static_CallRipemd160_3_postfixed0Filler.json
state_tests/stStaticCall/static_CallRipemd160_3_prefixed0Filler.json
state_tests/stStaticCall/static_CallRipemd160_4Filler.json
state_tests/stStaticCall/static_CallRipemd160_4_gas719Filler.json
state_tests/stStaticCall/static_CallRipemd160_5Filler.json
state_tests/stStaticCall/static_CallSha256_1Filler.json
state_tests/stStaticCall/static_CallSha256_1_nonzeroValueFiller.json
state_tests/stStaticCall/static_CallSha256_2Filler.json
state_tests/stStaticCall/static_CallSha256_3Filler.json
state_tests/stStaticCall/static_CallSha256_3_postfix0Filler.json
state_tests/stStaticCall/static_CallSha256_3_prefix0Filler.json
state_tests/stStaticCall/static_CallSha256_4Filler.json
state_tests/stStaticCall/static_CallSha256_4_gas99Filler.json
state_tests/stStaticCall/static_CallSha256_5Filler.json

@manually-enhanced: Do not overwrite. Merged; outputs and gas are derived.
"""

import hashlib

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

IDENTITY = 0x4
SHA256 = 0x2
RIPEMD160 = 0x3
OUTPUT_SLOT = 0
SUCCESS_SLOT = 2
SHORT_WORD = 0xF34578907F
FULL_WORD = 2**256 - 1
LARGE_INPUT_SIZE = 1_000_000
VALUE = 19


def precompile_output(precompile: int, data: bytes) -> bytes:
    """Return the precompile's output for `data`."""
    if precompile == IDENTITY:
        return data
    if precompile == SHA256:
        return hashlib.sha256(data).digest()
    if precompile == RIPEMD160:
        return hashlib.new("ripemd160", data).digest().rjust(32, b"\0")
    raise ValueError(f"Unknown precompile: {precompile}")


def precompile_gas(fork: Fork, precompile: int, size: int) -> int:
    """Return the precompile's gas cost for `size` bytes of input."""
    gas_costs = fork.gas_costs()
    words = (size + 31) // 32
    if precompile == IDENTITY:
        return (
            gas_costs.PRECOMPILE_IDENTITY_BASE
            + gas_costs.PRECOMPILE_IDENTITY_PER_WORD * words
        )
    if precompile == SHA256:
        return (
            gas_costs.PRECOMPILE_SHA256_BASE
            + gas_costs.PRECOMPILE_SHA256_PER_WORD * words
        )
    if precompile == RIPEMD160:
        return (
            gas_costs.PRECOMPILE_RIPEMD160_BASE
            + gas_costs.PRECOMPILE_RIPEMD160_PER_WORD * words
        )
    raise ValueError(f"Unknown precompile: {precompile}")


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_CallIdentitiy_1Filler.json",
        "state_tests/stStaticCall/static_CallIdentity_1_nonzeroValueFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_CallIdentity_2Filler.json",
        "state_tests/stStaticCall/static_CallIdentity_3Filler.json",
        "state_tests/stStaticCall/static_CallIdentity_4Filler.json",
        "state_tests/stStaticCall/static_CallIdentity_4_gas17Filler.json",
        "state_tests/stStaticCall/static_CallIdentity_4_gas18Filler.json",
        "state_tests/stStaticCall/static_CallIdentity_5Filler.json",
        "state_tests/stStaticCall/static_CallRipemd160_1Filler.json",
        "state_tests/stStaticCall/static_CallRipemd160_2Filler.json",
        "state_tests/stStaticCall/static_CallRipemd160_3Filler.json",
        "state_tests/stStaticCall/static_CallRipemd160_3_postfixed0Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_CallRipemd160_3_prefixed0Filler.json",
        "state_tests/stStaticCall/static_CallRipemd160_4Filler.json",
        "state_tests/stStaticCall/static_CallRipemd160_4_gas719Filler.json",
        "state_tests/stStaticCall/static_CallRipemd160_5Filler.json",
        "state_tests/stStaticCall/static_CallSha256_1Filler.json",
        "state_tests/stStaticCall/static_CallSha256_1_nonzeroValueFiller.json",
        "state_tests/stStaticCall/static_CallSha256_2Filler.json",
        "state_tests/stStaticCall/static_CallSha256_3Filler.json",
        "state_tests/stStaticCall/static_CallSha256_3_postfix0Filler.json",
        "state_tests/stStaticCall/static_CallSha256_3_prefix0Filler.json",
        "state_tests/stStaticCall/static_CallSha256_4Filler.json",
        "state_tests/stStaticCall/static_CallSha256_4_gas99Filler.json",
        "state_tests/stStaticCall/static_CallSha256_5Filler.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "word, word_offset, size, gas_short, with_value",
    [
        pytest.param(None, 0, 0, 0, False, id="empty"),
        pytest.param(None, 0, 0, 0, True, id="empty_nonzero_value"),
        pytest.param(SHORT_WORD, 5, 37, 0, False, id="word_at_5"),
        pytest.param(SHORT_WORD, 0, 37, 0, False, id="word_at_0"),
        pytest.param(SHORT_WORD << 8, 0, 37, 0, False, id="postfix0"),
        pytest.param(FULL_WORD, 0, 32, 0, False, id="full_word"),
        pytest.param(FULL_WORD, 0, 32, 1, False, id="full_word_one_gas_short"),
        pytest.param(
            FULL_WORD, 0, LARGE_INPUT_SIZE, 0, False, id="large_input"
        ),
    ],
)
@pytest.mark.parametrize(
    "precompile",
    [
        pytest.param(IDENTITY, id="identity"),
        pytest.param(SHA256, id="sha256"),
        pytest.param(RIPEMD160, id="ripemd160"),
    ],
)
def test_static_call_hash_precompiles(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    precompile: int,
    word: int | None,
    word_offset: int,
    size: int,
    gas_short: int,
    with_value: bool,
) -> None:
    """
    Verify the success flag and output of a STATICCALL to a hash
    precompile given exactly its gas cost, or `gas_short` less.

    With `with_value`, the caller then CALLs and CALLCODEs the precompile
    with value, which only the CALL moves to it.
    """
    memory = bytearray(max(size, word_offset + 32))
    code = Bytecode()
    if word is not None:
        code += Op.MSTORE(word_offset, word)
        memory[word_offset : word_offset + 32] = word.to_bytes(32, "big")
    call_gas = precompile_gas(fork, precompile, size) - gas_short
    code += Op.SSTORE(
        SUCCESS_SLOT,
        Op.STATICCALL(
            gas=call_gas, address=precompile, args_size=size, ret_size=32
        ),
    ) + Op.SSTORE(OUTPUT_SLOT, Op.MLOAD(0))
    if with_value:
        code += Op.POP(Op.CALL(address=precompile, value=VALUE)) + Op.POP(
            Op.CALLCODE(address=precompile, value=VALUE)
        )
    target = pre.deploy_contract(code=code + Op.STOP, balance=2 * VALUE)

    tx = Transaction(sender=pre.fund_eoa(), to=target)

    succeeds = gas_short == 0
    output = (
        precompile_output(precompile, bytes(memory[:size]))[:32]
        if succeeds
        else b""
    )
    returned = bytearray(memory[:32])
    returned[: len(output)] = output
    post: dict = {
        target: Account(
            storage={
                SUCCESS_SLOT: int(succeeds),
                OUTPUT_SLOT: int.from_bytes(returned, "big"),
            },
            balance=VALUE if with_value else 2 * VALUE,
        )
    }
    if with_value:
        post[Address(precompile)] = Account(balance_change=VALUE)

    state_test(pre=pre, post=post, tx=tx)
