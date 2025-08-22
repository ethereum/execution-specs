"""
abstract: Tests [EIP-7883: ModExp Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-7883)
    Test cases for [EIP-7883: ModExp Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-7883).
"""

from typing import Dict

import pytest

from ethereum_test_checklists import EIPChecklist
from ethereum_test_tools import Alloc, StateTestFiller, Transaction
from ethereum_test_tools.vm.opcode import Opcodes as Op

from ...byzantium.eip198_modexp_precompile.helpers import ModExpInput
from .helpers import vectors_from_file
from .spec import Spec, ref_spec_7883

REFERENCE_SPEC_GIT_PATH = ref_spec_7883.git_path
REFERENCE_SPEC_VERSION = ref_spec_7883.version


@pytest.mark.parametrize(
    "modexp_input,modexp_expected,gas_old,gas_new",
    vectors_from_file("vectors.json"),
    ids=lambda v: v.name,
)
@pytest.mark.valid_from("Berlin")
def test_vectors_from_eip(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
):
    """Test ModExp gas cost using the test vectors from EIP-7883."""
    state_test(
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "modexp_input,modexp_expected,gas_old,gas_new",
    vectors_from_file("legacy.json"),
    ids=lambda v: v.name,
)
@pytest.mark.valid_from("Berlin")
def test_vectors_from_legacy_tests(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
):
    """Test ModExp gas cost using the test vectors from legacy tests."""
    state_test(
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "modexp_input,",
    [
        # These invalid inputs are from EIP-7823.
        # Ref: https://github.com/ethereum/EIPs/blob/master/EIPS/eip-7823.md#analysis
        pytest.param(
            bytes.fromhex("9e5faafc"),
            id="invalid-case-1",
        ),
        pytest.param(
            bytes.fromhex("85474728"),
            id="invalid-case-2",
        ),
        pytest.param(
            bytes.fromhex("9e281a98" + "00" * 54 + "021e19e0c9bab2400000"),
            id="invalid-case-3",
        ),
    ],
)
@pytest.mark.parametrize(
    "modexp_expected,call_succeeds",
    [
        pytest.param(bytes(), False),
    ],
)
@EIPChecklist.Precompile.Test.Inputs.AllZeros
@pytest.mark.valid_from("Berlin")
def test_modexp_invalid_inputs(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
):
    """Test ModExp gas cost with invalid inputs."""
    state_test(
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "modexp_input,modexp_expected,call_succeeds",
    [
        pytest.param(
            ModExpInput(
                base="FF" * (Spec.MAX_LENGTH_BYTES + 1),
                exponent="FF",
                modulus="FF",
            ),
            Spec.modexp_error,
            False,
            id="base-too-long",
        ),
        pytest.param(
            ModExpInput(
                base="FF",
                exponent="FF" * (Spec.MAX_LENGTH_BYTES + 1),
                modulus="FF",
            ),
            Spec.modexp_error,
            False,
            id="exponent-too-long",
        ),
        pytest.param(
            ModExpInput(
                base="FF",
                exponent="FF",
                modulus="FF" * (Spec.MAX_LENGTH_BYTES + 1),
            ),
            Spec.modexp_error,
            False,
            id="modulus-too-long",
        ),
        pytest.param(
            ModExpInput(
                base="FF" * (Spec.MAX_LENGTH_BYTES + 1),
                exponent="FF",
                modulus="FF" * (Spec.MAX_LENGTH_BYTES + 1),
            ),
            Spec.modexp_error,
            False,
            id="base-modulus-too-long",
        ),
    ],
)
@pytest.mark.valid_from("Osaka")
def test_modexp_boundary_inputs(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
):
    """Test ModExp boundary inputs."""
    state_test(
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "call_opcode",
    [
        Op.CALL,
        Op.STATICCALL,
        Op.DELEGATECALL,
        Op.CALLCODE,
    ],
)
@pytest.mark.parametrize(
    "modexp_input,modexp_expected",
    [
        pytest.param(Spec.modexp_input, Spec.modexp_expected, id="base-heavy"),
    ],
)
@EIPChecklist.Precompile.Test.CallContexts.Static
@EIPChecklist.Precompile.Test.CallContexts.Delegate
@EIPChecklist.Precompile.Test.CallContexts.Callcode
@EIPChecklist.Precompile.Test.CallContexts.Normal
@pytest.mark.valid_from("Berlin")
def test_modexp_call_operations(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
):
    """Test ModExp call related operations with EIP-7883."""
    state_test(
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "modexp_input,modexp_expected,precompile_gas_modifier,call_succeeds",
    [
        pytest.param(
            Spec.modexp_input,
            Spec.modexp_expected,
            1,
            True,
            id="extra_gas",
        ),
        pytest.param(
            Spec.modexp_input,
            Spec.modexp_expected,
            0,
            True,
            id="exact_gas",
        ),
        pytest.param(
            Spec.modexp_input,
            Spec.modexp_error,
            -1,
            False,
            id="insufficient_gas",
        ),
    ],
)
@EIPChecklist.Precompile.Test.ValueTransfer.Fee.Over
@EIPChecklist.Precompile.Test.ValueTransfer.Fee.Exact
@EIPChecklist.Precompile.Test.ValueTransfer.Fee.Under
@pytest.mark.valid_from("Berlin")
def test_modexp_gas_usage_contract_wrapper(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
):
    """Test ModExp gas cost with different gas modifiers using contract wrapper calls."""
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "modexp_input,modexp_expected,precompile_gas_modifier,call_succeeds",
    [
        pytest.param(
            Spec.modexp_input,
            Spec.modexp_expected,
            1,
            True,
            id="extra_gas",
        ),
        pytest.param(
            Spec.modexp_input,
            Spec.modexp_expected,
            0,
            True,
            id="exact_gas",
        ),
        pytest.param(
            Spec.modexp_input,
            Spec.modexp_error,
            -1,
            False,
            id="insufficient_gas",
        ),
    ],
)
@pytest.mark.valid_from("Berlin")
def test_modexp_used_in_transaction_entry_points(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    modexp_input: bytes,
    tx_gas_limit: int,
):
    """Test ModExp using in transaction entry points with different precompile gas modifiers."""
    tx = Transaction(
        to=Spec.MODEXP_ADDRESS,
        sender=pre.fund_eoa(),
        data=bytes(modexp_input),
        gas_limit=tx_gas_limit,
    )
    state_test(pre=pre, tx=tx, post={})


def create_modexp_variable_gas_test_cases():
    """
    Create test cases for ModExp variable gas cost testing.

    Returns:
        List of pytest.param objects for the test cases

    """
    # Test case definitions: (base, exponent, modulus, expected_result, test_id)
    test_cases = [
        ("", "", "", "", "Z0"),
        ("01" * 16, "00" * 16, "02" * 16, "00" * 15 + "01", "S0"),
        ("01" * 16, "00" * 15 + "03", "02" * 16, "01" * 16, "S1"),
        ("01" * 32, "FF" * 32, "02" * 32, "01" * 32, "S2"),
        ("01" * 16, "00" * 40, "02" * 16, "00" * 15 + "01", "S3"),
        ("01" * 16, "00" * 39 + "01", "02" * 16, "01" * 16, "S4"),
        ("01" * 24, "00", "02" * 8, "00" * 7 + "01", "S5"),
        ("01" * 8, "01", "02" * 24, "00" * 16 + "01" * 8, "S6"),
        ("01" * 40, "00" * 16, "02" * 40, "00" * 39 + "01", "L0"),
        ("01" * 40, "FF" * 32, "02" * 40, "01" * 40, "L1"),
        ("01" * 40, "00" * 40, "02" * 40, "00" * 39 + "01", "L2"),
        ("01" * 40, "00" * 39 + "01", "02" * 40, "01" * 40, "L3"),
        ("01" * 48, "01", "02" * 16, "01" * 16, "L4"),
        ("01" * 16, "00" * 40, "02" * 48, "00" * 47 + "01", "L5"),
        # Critical 32-byte boundary cases
        ("01" * 31, "01", "02" * 33, "00" * 2 + "01" * 31, "B1"),
        ("01" * 33, "01", "02" * 31, "00" * 29 + "01" * 2, "B2"),
        ("01" * 33, "01", "02" * 33, "01" * 33, "B4"),
        # Zero value edge cases
        ("00" * 32, "00" * 32, "01" * 32, "00" * 31 + "01", "Z1"),
        ("01" * 32, "00" * 32, "00" * 32, "00" * 32, "Z2"),
        ("00" * 32, "01" * 32, "02" * 32, "00" * 32, "Z3"),
        # Maximum value stress tests
        ("FF" * 64, "FF" * 64, "FF" * 64, "00" * 64, "M1"),
        ("FF" * 32, "01", "FF" * 32, "00" * 32, "M2"),
        ("01", "FF" * 64, "FF" * 64, "00" * 63 + "01", "M3"),
        # Tiny maximum values
        ("FF", "FE", "FD", "47", "T2"),
        # Bit pattern cases
        ("01" * 32, "80" * 32, "02" * 32, "01" * 32, "P2"),
        ("01" * 33, "00" * 31 + "80" + "00", "02" * 33, "01" * 33, "P3"),
        # Asymmetric length cases
        ("01", "00" * 64, "02" * 64, "00" * 63 + "01", "A1"),
        ("01" * 64, "01", "02", "01", "A2"),
        ("01" * 64, "00" * 64, "02", "01", "A3"),
        # Word boundary case
        ("01" * 8, "01", "02" * 8, "0101010101010101", "W2"),
        # Exponent edge cases
        ("01" * 16, "00" * 32 + "01", "02" * 16, "01" * 16, "E1"),
        ("01" * 16, "80" + "00" * 31, "02" * 16, "01" * 16, "E2"),
        ("01" * 16, "00" * 31 + "80", "02" * 16, "01" * 16, "E3"),
        ("01" * 16, "7F" + "FF" * 31, "02" * 16, "01" * 16, "E4"),
    ]

    # Gas calculation parameters:
    #
    # Please refer to EIP-7883 for details of each function in the gas calculation.
    # Link: https://eips.ethereum.org/EIPS/eip-7883
    #
    # - calculate_multiplication_complexity:
    #   - Comp: if max_length <= 32 bytes, it is Small (S), otherwise it is Large (L)
    #   - Rel (Length Relation): base < modulus (<), base = modulus (=), base > modulus (>)
    #
    # - calculate_iteration_count
    #   - Iter (Iteration Case):
    #     - A: exp≤32 and exp=0
    #     - B: exp≤32 and exp≠0
    #     - C: exp>32 and low256=0
    #     - D: exp>32 and low256≠0
    #
    # - calculate_gas_cost
    #   - Clamp: True if raw gas < 500 (clamped to 500), False if raw gas ≥ 500 (no clamping)

    # Test case coverage table:
    # ┌─────┬──────┬─────┬──────┬───────┬─────────┬───────────────────────────────────────────────┐
    # │ ID  │ Comp │ Rel │ Iter │ Clamp │   Gas   │ Description                                   │
    # ├─────┼──────┼─────┼──────┼───────┼─────────┼───────────────────────────────────────────────┤
    # │ Z0  │  -   │  -  │  -   │  -    │   500   │ Zero case – empty inputs                      │
    # │ S0  │  S   │  =  │  A   │ True  │   500   │ Small, equal, zero exp, clamped               │
    # │ S1  │  S   │  =  │  B   │ True  │   500   │ Small, equal, small exp, clamped              │
    # │ S2  │  S   │  =  │  B   │ False │  4080   │ Small, equal, large exp, unclamped            │
    # │ S3  │  S   │  =  │  C   │ False │  2032   │ Small, equal, large exp + zero low256         │
    # │ S4  │  S   │  =  │  D   │ False │  2048   │ Small, equal, large exp + non-zero low256     │
    # │ S5  │  S   │  >  │  A   │ True  │   500   │ Small, base > mod, zero exp, clamped          │
    # │ S6  │  S   │  <  │  B   │ True  │   500   │ Small, base < mod, small exp, clamped         │
    # │ L0  │  L   │  =  │  A   │ True  │   500   │ Large, equal, zero exp, clamped               │
    # │ L1  │  L   │  =  │  B   │ False │ 12750   │ Large, equal, large exp, unclamped            │
    # │ L2  │  L   │  =  │  C   │ False │  6350   │ Large, equal, large exp + zero low256         │
    # │ L3  │  L   │  =  │  D   │ False │  6400   │ Large, equal, large exp + non-zero low256     │
    # │ L4  │  L   │  >  │  B   │ True  │   500   │ Large, base > mod, small exp, clamped         │
    # │ L5  │  L   │  <  │  C   │ False │  9144   │ Large, base < mod, large exp + zero low256    │
    # │ B1  │  L   │  <  │  B   │ True  │   500   │ Cross 32-byte boundary (31/33)                │
    # │ B2  │  L   │  >  │  B   │ True  │   500   │ Cross 32-byte boundary (33/31)                │
    # │ B4  │  L   │  =  │  B   │ True  │   500   │ Just over 32-byte boundary                    │
    # │ Z1  │  S   │  =  │  A   │ True  │   500   │ All zeros except modulus                      │
    # │ Z2  │  S   │  =  │  A   │ True  │   500   │ Zero modulus special case                     │
    # │ Z3  │  S   │  =  │  B   │ False │  3968   │ Zero base, large exponent                     │
    # │ M1  │  L   │  =  │  D   │ False │ 98176   │ Maximum values stress test                    │
    # │ M2  │  S   │  =  │  B   │ True  │   500   │ Max base/mod, small exponent                  │
    # │ M3  │  L   │  <  │  D   │ False │ 98176   │ Small base, max exponent/mod                  │
    # │ T2  │  S   │  =  │  B   │ True  │   500   │ Tiny maximum values                           │
    # │ P2  │  S   │  =  │  B   │ False │  4080   │ High bit in exponent                          │
    # │ P3  │  L   │  =  │  D   │ False │  1550   │ Specific bit pattern in large exponent        │
    # │ A1  │  L   │  <  │  C   │ False │ 65408   │ Asymmetric: tiny base, large exp/mod          │
    # │ A2  │  L   │  >  │  B   │ True  │   500   │ Asymmetric: large base, tiny exp/mod          │
    # │ A3  │  L   │  >  │  C   │ False │ 65408   │ Asymmetric: large base/exp, tiny modulus      │
    # │ W2  │  S   │  =  │  B   │ True  │   500   │ Exactly 8-byte words                          │
    # │ E1  │  S   │  =  │  D   │ True  │   500   │ Exponent exactly 33 bytes                     │
    # │ E2  │  S   │  =  │  B   │ False │  4080   │ High bit in exponent first byte               │
    # │ E3  │  S   │  =  │  B   │ True  │   500   │ High bit in exponent last byte                │
    # │ E4  │  S   │  =  │  B   │ False │  4064   │ Maximum 32-byte exponent                      │
    # └─────┴──────┴─────┴──────┴───────┴─────────┴───────────────────────────────────────────────┘
    for base, exponent, modulus, expected_result, test_id in test_cases:
        yield pytest.param(
            ModExpInput(base=base, exponent=exponent, modulus=modulus),
            bytes.fromhex(expected_result),
            id=test_id,
        )


@pytest.mark.parametrize(
    "modexp_input,modexp_expected",
    create_modexp_variable_gas_test_cases(),
)
@pytest.mark.valid_from("Berlin")
def test_modexp_variable_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
):
    """Test ModExp variable gas cost."""
    state_test(pre=pre, tx=tx, post=post)
