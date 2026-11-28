"""
Call the SHA256 and RIPEMD160 precompiles with CALL and CALLCODE.

Ported from:
state_tests/stPreCompiledContracts2/CallSha256_0Filler.json
state_tests/stPreCompiledContracts2/CallSha256_1Filler.json
state_tests/stPreCompiledContracts2/CallSha256_1_nonzeroValueFiller.json
state_tests/stPreCompiledContracts2/CallSha256_2Filler.json
state_tests/stPreCompiledContracts2/CallSha256_3Filler.json
state_tests/stPreCompiledContracts2/CallSha256_3_postfix0Filler.json
state_tests/stPreCompiledContracts2/CallSha256_3_prefix0Filler.json
state_tests/stPreCompiledContracts2/CallSha256_4Filler.json
state_tests/stPreCompiledContracts2/CallSha256_4_gas99Filler.json
state_tests/stPreCompiledContracts2/CallSha256_5Filler.json
state_tests/stPreCompiledContracts2/CallRipemd160_1Filler.json
state_tests/stPreCompiledContracts2/CallRipemd160_2Filler.json
state_tests/stPreCompiledContracts2/CallRipemd160_3Filler.json
state_tests/stPreCompiledContracts2/CallRipemd160_3_postfixed0Filler.json
state_tests/stPreCompiledContracts2/CallRipemd160_3_prefixed0Filler.json
state_tests/stPreCompiledContracts2/CallRipemd160_4Filler.json
state_tests/stPreCompiledContracts2/CallRipemd160_4_gas719Filler.json
state_tests/stPreCompiledContracts2/CallRipemd160_5Filler.json
state_tests/stPreCompiledContracts2/CALLCODESha256_0Filler.json
state_tests/stPreCompiledContracts2/CALLCODESha256_1Filler.json
state_tests/stPreCompiledContracts2/CALLCODESha256_1_nonzeroValueFiller.json
state_tests/stPreCompiledContracts2/CALLCODESha256_2Filler.json
state_tests/stPreCompiledContracts2/CALLCODESha256_3Filler.json
state_tests/stPreCompiledContracts2/CALLCODESha256_3_postfix0Filler.json
state_tests/stPreCompiledContracts2/CALLCODESha256_3_prefix0Filler.json
state_tests/stPreCompiledContracts2/CALLCODESha256_4Filler.json
state_tests/stPreCompiledContracts2/CALLCODESha256_4_gas99Filler.json
state_tests/stPreCompiledContracts2/CALLCODESha256_5Filler.json
state_tests/stPreCompiledContracts2/CALLCODERipemd160_0Filler.json
state_tests/stPreCompiledContracts2/CALLCODERipemd160_1Filler.json
state_tests/stPreCompiledContracts2/CALLCODERipemd160_2Filler.json
state_tests/stPreCompiledContracts2/CALLCODERipemd160_3Filler.json
state_tests/stPreCompiledContracts2/CALLCODERipemd160_3_postfixed0Filler.json
state_tests/stPreCompiledContracts2/CALLCODERipemd160_3_prefixed0Filler.json
state_tests/stPreCompiledContracts2/CALLCODERipemd160_4Filler.json
state_tests/stPreCompiledContracts2/CALLCODERipemd160_4_gas719Filler.json
state_tests/stPreCompiledContracts2/CALLCODERipemd160_5Filler.json

@manually-enhanced: Do not overwrite. Digests and gas boundaries are
derived; the `3_prefix0` fillers equal `3` (the leading zero is lost
in the MSTORE word) and are covered by it.
"""

import hashlib
from typing import Callable

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 12
VALUE = 0x13
INPUT_WORD = 0xF34578907F
FULL_WORD = 2**256 - 1
FIXED_GAS = 0xFF
HUGE_INPUT_SIZE = 1_000_000


def sha256(data: bytes) -> int:
    """Return the SHA256 precompile output as a word."""
    return int.from_bytes(hashlib.sha256(data).digest(), "big")


def ripemd160(data: bytes) -> int:
    """Return the RIPEMD160 precompile output as a word."""
    return int.from_bytes(hashlib.new("ripemd160", data).digest(), "big")


def word(value: int) -> bytes:
    """Return `value` as a 32-byte word."""
    return value.to_bytes(32, "big")


@pytest.mark.ported_from(
    [
        "state_tests/stPreCompiledContracts2/CallSha256_0Filler.json",
        "state_tests/stPreCompiledContracts2/CallSha256_1Filler.json",
        "state_tests/stPreCompiledContracts2/CallSha256_1_nonzeroValueFiller.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CallSha256_2Filler.json",
        "state_tests/stPreCompiledContracts2/CallSha256_3Filler.json",
        "state_tests/stPreCompiledContracts2/CallSha256_3_postfix0Filler.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CallSha256_3_prefix0Filler.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CallSha256_4Filler.json",
        "state_tests/stPreCompiledContracts2/CallSha256_4_gas99Filler.json",
        "state_tests/stPreCompiledContracts2/CallSha256_5Filler.json",
        "state_tests/stPreCompiledContracts2/CallRipemd160_1Filler.json",
        "state_tests/stPreCompiledContracts2/CallRipemd160_2Filler.json",
        "state_tests/stPreCompiledContracts2/CallRipemd160_3Filler.json",
        "state_tests/stPreCompiledContracts2/CallRipemd160_3_postfixed0Filler.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CallRipemd160_3_prefixed0Filler.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CallRipemd160_4Filler.json",
        "state_tests/stPreCompiledContracts2/CallRipemd160_4_gas719Filler.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CallRipemd160_5Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODESha256_0Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODESha256_1Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODESha256_1_nonzeroValueFiller.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CALLCODESha256_2Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODESha256_3Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODESha256_3_postfix0Filler.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CALLCODESha256_3_prefix0Filler.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CALLCODESha256_4Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODESha256_4_gas99Filler.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CALLCODESha256_5Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODERipemd160_0Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODERipemd160_1Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODERipemd160_2Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODERipemd160_3Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODERipemd160_3_postfixed0Filler.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CALLCODERipemd160_3_prefixed0Filler.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CALLCODERipemd160_4Filler.json",
        "state_tests/stPreCompiledContracts2/CALLCODERipemd160_4_gas719Filler.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CALLCODERipemd160_5Filler.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "case",
    [
        "0",
        "1",
        "1_nonzero_value",
        "2",
        "3",
        "3_postfix0",
        "4",
        "4_short_gas",
        "5",
    ],
)
@pytest.mark.parametrize("precompile", ["sha256", "ripemd160"])
@pytest.mark.parametrize("opcode", [Op.CALL, Op.CALLCODE])
def test_hash_precompiles(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    precompile: str,
    case: str,
) -> None:
    """Hash the memory input and store the output word and success flag."""
    gas_costs = fork.gas_costs()
    address: Address
    digest: Callable[[bytes], int]
    if precompile == "sha256":
        address = Address(0x02)
        digest = sha256
        base = gas_costs.PRECOMPILE_SHA256_BASE
        per_word = gas_costs.PRECOMPILE_SHA256_PER_WORD
    elif precompile == "ripemd160":
        address = Address(0x03)
        digest = ripemd160
        base = gas_costs.PRECOMPILE_RIPEMD160_BASE
        per_word = gas_costs.PRECOMPILE_RIPEMD160_PER_WORD
    else:
        raise ValueError(f"unknown precompile {precompile}")

    def cost(size: int) -> int:
        return base + per_word * ((size + 31) // 32)

    setup: Bytecode = Bytecode()
    memory = b""
    value = 0
    if case == "0":
        setup = Op.MSTORE(offset=0x0, value=0x1)
        memory = word(1)
        size, gas = 0x20, FIXED_GAS
    elif case in ("1", "1_nonzero_value"):
        size, gas = 0, cost(0)
        if case == "1_nonzero_value":
            value = VALUE
    elif case == "2":
        setup = Op.MSTORE(offset=0x5, value=INPUT_WORD)
        memory = bytes(5) + word(INPUT_WORD)
        size, gas = 37, cost(37)
    elif case in ("3", "3_postfix0"):
        stored = INPUT_WORD if case == "3" else INPUT_WORD << 8
        setup = Op.MSTORE(offset=0x0, value=stored)
        memory = word(stored)
        size, gas = 37, cost(37)
    elif case in ("4", "4_short_gas"):
        setup = Op.MSTORE(offset=0x0, value=FULL_WORD)
        memory = word(FULL_WORD)
        size, gas = 0x20, cost(0x20) - (case == "4_short_gas")
    elif case == "5":
        setup = Op.MSTORE(offset=0x0, value=FULL_WORD)
        memory = word(FULL_WORD)
        size, gas = HUGE_INPUT_SIZE, cost(HUGE_INPUT_SIZE) - 1
    else:
        raise ValueError(f"unknown case {case}")

    data = memory[:size].ljust(size, b"\0")
    success = gas >= cost(size)
    first_word = int.from_bytes(memory[:32].ljust(32, b"\0"), "big")
    output = digest(data) if success else first_word

    code = (
        setup
        + Op.SSTORE(
            key=0x2,
            value=opcode(
                gas=gas,
                address=address,
                value=value,
                args_size=size,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
    )
    sender = pre.fund_eoa()
    target = pre.deploy_contract(
        code=code,
        storage={0: SENTINEL, 2: SENTINEL},
        balance=value,
    )

    tx = Transaction(sender=sender, to=target)

    storage = {0: output, 2: int(success)}
    post = {target: Account(storage=storage)}
    if value and opcode == Op.CALL:
        post = {
            target: Account(storage=storage, balance=0),
            address: Account(balance=value),
        }

    state_test(pre=pre, post=post, tx=tx)
