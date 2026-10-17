"""
EIP-12504 test vectors.

Every row of the EIP's Test Cases table: the instruction is given its
inputs with PUSHes, top of stack last, and its output is stored at slot 0.
The expected output is the 64-bit result, zero-extended.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import ref_spec_12504
from .vectors import VECTORS

REFERENCE_SPEC_GIT_PATH = ref_spec_12504.git_path
REFERENCE_SPEC_VERSION = ref_spec_12504.version

pytestmark = pytest.mark.valid_from("EIP12504")

SLOT_RESULT = 0
TX_GAS_LIMIT = 1_000_000


@pytest.mark.parametrize(
    "name,inputs,output",
    [
        pytest.param(name, inputs, output, id=f"{name}_{i}")
        for i, (name, inputs, output) in enumerate(VECTORS)
    ],
)
def test_vectors(
    state_test: StateTestFiller,
    pre: Alloc,
    name: str,
    inputs: List[int],
    output: int,
) -> None:
    """Run one vector of the EIP's table and store the result."""
    op = getattr(Op, name)
    code = Op.SSTORE(SLOT_RESULT, op(*inputs)) + Op.STOP
    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {contract: Account(storage={SLOT_RESULT: output})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "name,inputs",
    [
        pytest.param("ADD64", [2**256 - 1, 2**256 - 1], id="ADD64"),
        pytest.param("MUL64", [2**256 - 1, 2**256 - 1], id="MUL64"),
        pytest.param("NOT64", [0], id="NOT64"),
        pytest.param("SAR64", [1, 2**255], id="SAR64"),
        pytest.param("SIGNEXTEND64", [0, 2**255 | 0x80], id="SIGNEXTEND64"),
        pytest.param("EXP64", [2**256 - 1, 3], id="EXP64"),
    ],
)
def test_high_bits_are_zero(
    state_test: StateTestFiller,
    pre: Alloc,
    name: str,
    inputs: List[int],
) -> None:
    """
    The high 192 bits of every result are zero, whatever the inputs: the
    result shifted right by 64 is zero.
    """
    op = getattr(Op, name)
    code = Op.SSTORE(SLOT_RESULT, Op.SHR(64, op(*inputs))) + Op.STOP
    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {contract: Account(storage={SLOT_RESULT: 0})}
    state_test(pre=pre, post=post, tx=tx)
