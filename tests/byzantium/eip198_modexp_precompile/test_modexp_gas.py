"""
Gas cost tests for the
[EIP-198: MODEXP Precompile](https://eips.ethereum.org/EIPS/eip-198).

The gas charged for a call is pinned by giving the precompile exactly its
cost and one gas less, over operand lengths that select each branch of the
multiplication complexity formula. EIP-2565 replaces that formula in Berlin,
so the same cases also pin its schedule. The EIP-7883 schedule that follows
in Osaka is covered by the tests of that EIP.
"""

from typing import Dict

import pytest
from execution_testing import Alloc, StateTestFiller, Transaction

from .helpers import ModExpInput

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-198.md"
REFERENCE_SPEC_VERSION = "5c8f066acb210c704ef80c1033a941aa5374aac5"


@pytest.mark.parametrize(
    "modexp_input,modexp_expected",
    [
        pytest.param(
            ModExpInput(base="ff" * 64, exponent="ff" * 32, modulus="07"),
            bytes.fromhex("06"),
            id="quadratic_branch_edge",
        ),
        pytest.param(
            ModExpInput(base="ff" * 65, exponent="ff" * 32, modulus="07"),
            bytes.fromhex("01"),
            id="linear_branch_edge",
        ),
        pytest.param(
            ModExpInput(base="ff" * 1024, exponent="03", modulus="07"),
            bytes.fromhex("06"),
            id="linear_branch_max",
        ),
        pytest.param(
            ModExpInput(base="ff" * 1025, exponent="03", modulus="07"),
            bytes.fromhex("01"),
            id="beyond_linear_branch",
        ),
    ],
)
@pytest.mark.parametrize(
    "precompile_gas_modifier,call_succeeds",
    [
        pytest.param(0, True, id="exact_gas"),
        pytest.param(-1, False, id="insufficient_gas"),
    ],
)
@pytest.mark.valid_from("Byzantium")
@pytest.mark.valid_until("Prague")
def test_modexp_gas_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
) -> None:
    """
    Call ModExp with exactly its gas cost and with one gas less, over the
    operand lengths that select each branch of the multiplication complexity
    formula: the quadratic branch and its upper edge at 64 bytes, the linear
    branch from 65 bytes to its upper edge at 1024 bytes, and the branch
    beyond that.
    """
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "modexp_input,modexp_expected",
    [
        pytest.param(
            ModExpInput(base="", exponent="", modulus=""),
            bytes(),
            id="empty_operands",
        ),
    ],
)
@pytest.mark.valid_from("Byzantium")
@pytest.mark.valid_until("Prague")
def test_modexp_minimum_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
) -> None:
    """
    Call ModExp over empty operands with exactly its gas cost, which is zero
    until EIP-2565 introduces a minimum charge of 200 gas.
    """
    state_test(pre=pre, tx=tx, post=post)
