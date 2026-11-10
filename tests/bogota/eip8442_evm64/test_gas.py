"""
EIP-8442 gas costs.

Each instruction is metered between two GAS instructions, and the
difference, less the known costs of the PUSHes, the POP, and the second
GAS, is its cost.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import Spec, ref_spec_8442
from .vectors import EXP64_GAS, POPS, STATIC_GAS

REFERENCE_SPEC_GIT_PATH = ref_spec_8442.git_path
REFERENCE_SPEC_VERSION = ref_spec_8442.version

pytestmark = pytest.mark.valid_from("EIP8442")

SLOT_RESULT = 0
TX_GAS_LIMIT = 1_000_000

PUSH_GAS = 3
POP_GAS = 2
GAS_GAS = 2

# Operands that are small, nonzero, and safe for every instruction.
OPERAND = 0x1234


def metered(op: Bytecode, inputs: int, pops_result: bool) -> Bytecode:
    """
    Return code that runs `op` on `inputs` PUSH8 operands between two GAS
    instructions and stores the difference at ``SLOT_RESULT``.
    """
    code = Bytecode() + Op.GAS
    for _ in range(inputs):
        code += Op.PUSH8[OPERAND]
    code += op
    if pops_result:
        code += Op.POP
    # Stack: gas_before, gas_after; store gas_before - gas_after.
    code += Op.GAS + Op.SWAP1 + Op.SUB + Op.PUSH0 + Op.SSTORE
    return code


def overhead(inputs: int, pops_result: bool) -> int:
    """The gas of the PUSHes, the POP if any, and the second GAS."""
    return PUSH_GAS * inputs + (POP_GAS if pops_result else 0) + GAS_GAS


@pytest.mark.parametrize(
    "name,gas",
    [pytest.param(name, gas, id=name) for name, gas in STATIC_GAS.items()],
)
def test_static_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    name: str,
    gas: int,
) -> None:
    """Each instruction with a static cost costs its tier."""
    op = getattr(Op, name)
    inputs = POPS[name]
    code = metered(op, inputs, pops_result=True)
    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {
        contract: Account(
            storage={SLOT_RESULT: gas + overhead(inputs, pops_result=True)}
        )
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "base,exponent,gas",
    [pytest.param(b, e, g, id=f"exponent_{e:#x}") for (b, e), g in EXP64_GAS],
)
def test_exp64_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    base: int,
    exponent: int,
    gas: int,
) -> None:
    """
    EXP64 costs 5 plus 25 per byte of the exponent, the exponent read
    modulo 2**64.
    """
    code = (
        Op.GAS
        + Op.PUSH32[exponent]
        + Op.PUSH32[base]
        + Op.EXP64
        + Op.POP
        + Op.GAS
        + Op.SWAP1
        + Op.SUB
        + Op.PUSH0
        + Op.SSTORE
    )
    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {
        contract: Account(
            storage={SLOT_RESULT: gas + overhead(2, pops_result=True)}
        )
    }
    state_test(pre=pre, post=post, tx=tx)
    assert gas == Spec.EXP64_BASE + Spec.EXP64_PER_BYTE * (
        ((exponent % 2**64).bit_length() + 7) // 8
    )


@pytest.mark.parametrize(
    "name,inputs,expansion",
    [
        # Fresh memory; a 32-byte window at offset 0 is one word: 3 gas.
        pytest.param("MLOAD64", 1, 3, id="MLOAD64_one_word"),
        pytest.param("MSTORE64", 2, 3, id="MSTORE64_one_word"),
    ],
)
def test_memory_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    name: str,
    inputs: int,
    expansion: int,
) -> None:
    """MLOAD64 and MSTORE64 cost 2 plus memory expansion, as their twins."""
    op = getattr(Op, name)
    pops_result = name == "MLOAD64"
    # Offset 0, and for MSTORE64 a value beneath it.
    code = Bytecode() + Op.GAS
    if inputs == 2:
        code += Op.PUSH8[OPERAND]
    code += Op.PUSH0 + op
    if pops_result:
        code += Op.POP
    code += Op.GAS + Op.SWAP1 + Op.SUB + Op.PUSH0 + Op.SSTORE
    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    push_gas = PUSH_GAS * (inputs - 1) + 2  # PUSH8s, and the PUSH0 offset
    expected = (
        Spec.VERY_LOW_64
        + expansion
        + push_gas
        + (POP_GAS if pops_result else 0)
        + GAS_GAS
    )
    post = {contract: Account(storage={SLOT_RESULT: expected})}
    state_test(pre=pre, post=post, tx=tx)
