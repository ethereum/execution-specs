"""
EIP-7883 ModExp gas cost increase tests.

Tests for ModExp gas cost increase in
[EIP-7883: ModExp Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-7883).
"""

from typing import Dict, Generator

import pytest

from ethereum_test_checklists import EIPChecklist
from ethereum_test_forks import Fork, Osaka
from ethereum_test_tools import (
    Alloc,
    Environment,
    StateTestFiller,
    Storage,
    Transaction,
    keccak256,
)
from ethereum_test_types.helpers import compute_create_address
from ethereum_test_vm import Opcodes as Op

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
@EIPChecklist.Precompile.Test.Inputs.Valid()
@EIPChecklist.Precompile.Test.InputLengths.Dynamic.Valid()
@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.valid_from("Berlin")
@pytest.mark.slow()
def test_vectors_from_eip(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
) -> None:
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
@EIPChecklist.Precompile.Test.Inputs.Invalid()
@pytest.mark.valid_from("Berlin")
def test_vectors_from_legacy_tests(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
) -> None:
    """Test ModExp gas cost using the test vectors from legacy tests."""
    state_test(
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "modexp_input,",
    [
        # These invalid inputs are from EIP-7823. Ref:
        # https://github.com/ethereum/EIPs/blob/master/EIPS/eip-7823.md#analysis
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
    ids=[""],
)
@EIPChecklist.Precompile.Test.Inputs.AllZeros
@pytest.mark.valid_from("Berlin")
def test_modexp_invalid_inputs(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
) -> None:
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
@EIPChecklist.Precompile.Test.OutOfBounds.MaxPlusOne()
@EIPChecklist.Precompile.Test.Inputs.Invalid.Corrupted()
@EIPChecklist.Precompile.Test.Inputs.Invalid()
@EIPChecklist.Precompile.Test.InputLengths.Dynamic.TooLong()
@pytest.mark.valid_from("Osaka")
def test_modexp_boundary_inputs(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
) -> None:
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
@EIPChecklist.Precompile.Test.CallContexts.Static()
@EIPChecklist.Precompile.Test.CallContexts.Delegate()
@EIPChecklist.Precompile.Test.CallContexts.Callcode()
@EIPChecklist.Precompile.Test.CallContexts.Normal()
@pytest.mark.valid_from("Berlin")
def test_modexp_call_operations(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
) -> None:
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
        pytest.param(
            Spec.modexp_input,
            Spec.modexp_expected,
            float("inf"),
            True,
            id="excessive_gas",
        ),
    ],
)
@EIPChecklist.Precompile.Test.GasUsage.Dynamic()
@EIPChecklist.Precompile.Test.ExcessiveGasUsage()
@pytest.mark.valid_from("Berlin")
def test_modexp_gas_usage_contract_wrapper(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
) -> None:
    """
    Test ModExp gas cost with different gas modifiers using contract wrapper
    calls.
    """
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "modexp_input,modexp_expected,precompile_gas_modifier,call_values,call_succeeds",
    [
        pytest.param(
            Spec.modexp_input,
            Spec.modexp_expected,
            1,
            0,
            True,
            id="extra_gas",
        ),
        pytest.param(
            Spec.modexp_input,
            Spec.modexp_expected,
            0,
            0,
            True,
            id="exact_gas",
        ),
        pytest.param(
            Spec.modexp_input,
            Spec.modexp_expected,
            0,
            1000,
            True,
            id="extra_value",
        ),
        pytest.param(
            Spec.modexp_input,
            Spec.modexp_error,
            -1,
            0,
            False,
            id="insufficient_gas",
        ),
    ],
)
@EIPChecklist.Precompile.Test.CallContexts.TxEntry()
@EIPChecklist.Precompile.Test.ValueTransfer.NoFee()
@pytest.mark.valid_from("Berlin")
def test_modexp_used_in_transaction_entry_points(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    modexp_input: bytes,
    tx_gas_limit: int,
    call_values: int,
) -> None:
    """
    Test ModExp using in transaction entry points with different precompile gas
    modifiers.
    """
    tx = Transaction(
        to=Spec.MODEXP_ADDRESS,
        sender=pre.fund_eoa(),
        data=bytes(modexp_input),
        gas_limit=tx_gas_limit,
        value=call_values,
    )
    state_test(pre=pre, tx=tx, post={})


@pytest.mark.parametrize(
    "modexp_input,modexp_expected",
    [
        pytest.param(
            Spec.modexp_input,
            Spec.modexp_expected,
            id="valid_input",
        )
    ],
)
@EIPChecklist.Precompile.Test.CallContexts.Initcode()
@pytest.mark.valid_from("Berlin")
def test_contract_creation_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
    modexp_input: bytes,
    modexp_expected: bytes,
) -> None:
    """Test the contract creation for the ModExp precompile."""
    sender = pre.fund_eoa()

    storage = Storage()

    contract_address = compute_create_address(address=sender, nonce=0)
    contract_bytecode = (
        Op.CODECOPY(0, Op.SUB(Op.CODESIZE, len(bytes(modexp_input))), len(bytes(modexp_input)))
        + Op.CALL(
            gas=1_000_000,
            address=Spec.MODEXP_ADDRESS,
            value=0,
            args_offset=0,
            args_size=len(bytes(modexp_input)),
            ret_offset=0,
            ret_size=len(bytes(modexp_expected)),
        )
        + Op.SSTORE(storage.store_next(True), Op.DUP1())
        + Op.SSTORE(
            storage.store_next(keccak256(bytes(modexp_expected))), Op.SHA3(0, Op.RETURNDATASIZE())
        )
        + Op.SSTORE(storage.store_next(len(bytes(modexp_expected))), Op.RETURNDATASIZE())
        + Op.STOP
    )

    tx = Transaction(
        sender=sender,
        gas_limit=1_000_000,
        to=None,
        value=0,
        data=contract_bytecode + bytes(modexp_input),
    )

    post = {
        contract_address: {
            "storage": storage,
        }
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "modexp_input,modexp_expected",
    [
        pytest.param(
            Spec.modexp_input,
            Spec.modexp_expected,
            id="valid_input",
        ),
    ],
)
@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2])
@EIPChecklist.Precompile.Test.CallContexts.Initcode.CREATE()
@pytest.mark.valid_from("Berlin")
def test_contract_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
    modexp_input: bytes,
    modexp_expected: bytes,
    opcode: Op,
) -> None:
    """Test ModExp behavior from contract creation."""
    sender = pre.fund_eoa()

    storage = Storage()

    call_modexp_bytecode = (
        Op.CODECOPY(0, Op.SUB(Op.CODESIZE, len(bytes(modexp_input))), len(bytes(modexp_input)))
        + Op.CALL(
            gas=200_000,
            address=Spec.MODEXP_ADDRESS,
            value=0,
            args_offset=0,
            args_size=len(bytes(modexp_input)),
            ret_offset=0,
            ret_size=len(bytes(modexp_expected)),
        )
        + Op.SSTORE(storage.store_next(True), Op.DUP1())
        + Op.SSTORE(
            storage.store_next(keccak256(bytes(modexp_expected))), Op.SHA3(0, Op.RETURNDATASIZE())
        )
        + Op.SSTORE(storage.store_next(len(bytes(modexp_expected))), Op.RETURNDATASIZE())
        + Op.STOP
    )
    full_initcode = call_modexp_bytecode + bytes(modexp_input)
    total_bytecode_length = len(call_modexp_bytecode) + len(bytes(modexp_input))

    create_contract = (
        Op.CALLDATACOPY(offset=0, size=total_bytecode_length)
        + opcode(offset=0, size=total_bytecode_length)
        + Op.STOP
    )

    factory_contract_address = pre.deploy_contract(code=create_contract)
    contract_address = compute_create_address(
        address=factory_contract_address, nonce=1, initcode=full_initcode, opcode=opcode
    )

    tx = Transaction(
        sender=sender,
        gas_limit=200_000,
        to=factory_contract_address,
        value=0,
        data=call_modexp_bytecode + bytes(modexp_input),
    )

    post = {
        contract_address: {
            "storage": storage,
        }
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def create_modexp_variable_gas_test_cases() -> Generator:
    """
    Create test cases for ModExp variable gas cost testing.

    Returns: List of pytest.param objects for the test cases
    """
    # Test case definitions: (base, exponent, modulus, expected_result,
    # gas_usage, test_id)
    test_cases = [
        ("", "", "", "", 500, "Z0"),
        ("01" * 32, "00" * 32, "", "", 500, "Z1"),
        ("01" * 1024, "00" * 32, "", "", 32768, "Z2"),
        ("01" * 32, "00" * 1024, "", "", 253952, "Z3"),
        ("01" * 32, "00" * 1023 + "01", "", "", 253952, "Z4"),
        ("", "", "01" * 32, "00" * 31 + "01", 500, "Z5"),
        ("", "01" * 32, "01" * 32, "00" * 32, 3968, "Z6"),
        ("", "00" * 31 + "01", "01" * 1024, "00" * 1024, 32768, "Z7"),
        ("01" * 16, "00" * 16, "02" * 16, "00" * 15 + "01", 500, "S0"),
        ("01" * 16, "00" * 15 + "03", "02" * 16, "01" * 16, 500, "S1"),
        ("01" * 32, "FF" * 32, "02" * 32, "01" * 32, 4080, "S2"),
        ("01" * 16, "00" * 40, "02" * 16, "00" * 15 + "01", 2048, "S3"),
        ("01" * 16, "00" * 39 + "01", "02" * 16, "01" * 16, 2048, "S4"),
        ("01" * 24, "00", "02" * 8, "00" * 7 + "01", 500, "S5"),
        ("01" * 8, "01", "02" * 24, "00" * 16 + "01" * 8, 500, "S6"),
        ("01" * 40, "00" * 16, "02" * 40, "00" * 39 + "01", 500, "L0"),
        ("01" * 40, "FF" * 32, "02" * 40, "01" * 40, 12750, "L1"),
        ("01" * 40, "00" * 40, "02" * 40, "00" * 39 + "01", 6400, "L2"),
        ("01" * 40, "00" * 39 + "01", "02" * 40, "01" * 40, 6400, "L3"),
        ("01" * 48, "01", "02" * 16, "01" * 16, 500, "L4"),
        ("01" * 16, "00" * 40, "02" * 48, "00" * 47 + "01", 9216, "L5"),
        # Critical 32-byte boundary cases
        ("01" * 31, "01", "02" * 33, "00" * 2 + "01" * 31, 500, "B1"),
        ("01" * 33, "01", "02" * 31, "00" * 29 + "01" * 2, 500, "B2"),
        ("01" * 33, "01", "02" * 33, "01" * 33, 500, "B4"),
        # Zero value edge cases
        ("00" * 32, "00" * 32, "01" * 32, "00" * 31 + "01", 500, "Z8"),
        ("01" * 32, "00" * 32, "00" * 32, "00" * 32, 500, "Z9"),
        ("00" * 32, "01" * 32, "02" * 32, "00" * 32, 3968, "Z10"),
        ("00" * 32, "00" * 33, "01" * 32, "00" * 31 + "01", 500, "Z11"),
        ("00" * 32, "00" * 1024, "01" * 32, "00" * 31 + "01", 253952, "Z12"),
        ("00" * 1024, "00" * 32, "01" * 32, "00" * 31 + "01", 32768, "Z13"),
        ("01" * 32, "00" * 1024, "00" * 32, "00" * 32, 253952, "Z14"),
        ("01" * 32, "00" * 31 + "01", "00" * 1024, "00" * 1024, 32768, "Z15"),
        # Maximum value stress tests
        ("FF" * 64, "FF" * 64, "FF" * 64, "00" * 64, 98176, "M1"),
        ("FF" * 32, "01", "FF" * 32, "00" * 32, 500, "M2"),
        ("01", "FF" * 64, "FF" * 64, "00" * 63 + "01", 98176, "M3"),
        # Tiny maximum values
        ("FF", "FE", "FD", "47", 500, "T2"),
        # Bit pattern cases
        ("01" * 32, "80" * 32, "02" * 32, "01" * 32, 4080, "P2"),
        ("01" * 33, "00" * 31 + "80" + "00", "02" * 33, "01" * 33, 1150, "P3"),
        # Asymmetric length cases
        ("01", "00" * 64, "02" * 64, "00" * 63 + "01", 65536, "A1"),
        ("01" * 64, "01", "02", "01", 500, "A2"),
        ("01" * 64, "00" * 64, "02", "01", 65536, "A3"),
        # Word boundary case
        ("01" * 8, "01", "02" * 8, "0101010101010101", 500, "W2"),
        # Exponent edge cases
        ("01" * 16, "00" * 32 + "01", "02" * 16, "01" * 16, 500, "E1"),
        ("01" * 16, "80" + "00" * 31, "02" * 16, "01" * 16, 4080, "E2"),
        ("01" * 16, "00" * 31 + "80", "02" * 16, "01" * 16, 500, "E3"),
        ("01" * 16, "7F" + "FF" * 31, "02" * 16, "01" * 16, 4064, "E4"),
        # Implementation coverage cases
        # IC1: Bit shift vs multiplication at 33-byte boundary
        ("FF" * 33, "01", "FF" * 33, "00" * 33, 500, "IC1"),
        # IC3: Ceiling division at 7 bytes
        ("01" * 7, "01", "02" * 7, "01" * 7, 500, "IC3"),
        # IC4: Ceiling division at 9 bytes
        ("01" * 9, "01", "02" * 9, "01" * 9, 500, "IC4"),
        # IC5: Bit counting in middle of exponent
        ("01", "00" * 15 + "80" + "00" * 16, "02", "01", 2160, "IC5"),
        # IC6: Native library even byte optimization
        ("01" * 31 + "00", "01", "01" * 31 + "00", "00" * 32, 500, "IC6"),
        # IC7: Vector optimization 128-bit boundary
        ("00" * 15 + "01" * 17, "01", "00" * 15 + "01" * 17, "00" * 32, 500, "IC7"),
        # IC9: Zero modulus with large inputs
        ("FF" * 32, "FF" * 32, "", "", None, "IC9"),  # N/A case
        # IC10: Power-of-2 boundary with high bit
        ("01" * 32, "80" + "00" * 31, "02" * 32, "01" * 32, 4080, "IC10"),
    ]

    # Gas calculation parameters:
    #
    # Please refer to EIP-7883 for details of each function in the gas
    # calculation.
    # Link: https://eips.ethereum.org/EIPS/eip-7883
    #
    # - calculate_multiplication_complexity:
    #   - Comp: if max_length <= 32 bytes, it is Small (S), otherwise it is
    #       Large (L)
    #   - Rel (Length Relation): base < modulus (<), base = modulus (=),
    #       base > modulus (>)
    #
    # - calculate_iteration_count
    #   - Iter (Iteration Case):
    #     - A: exp≤32 and exp=0
    #     - B: exp≤32 and exp≠0
    #     - C: exp>32 and low256=0
    #     - D: exp>32 and low256≠0
    #
    # - calculate_gas_cost
    #   - Clamp: True if raw gas < 500 (clamped to 500), False if raw gas ≥ 500
    #       (no clamping)

    """
    Test case coverage table:

    ┌─────┬──────┬─────┬──────┬───────┬─────────┬───────────────────────────────────────────────┐
    │ ID  │ Comp │ Rel │ Iter │ Clamp │   Gas   │ Description                                   │
    ├─────┼──────┼─────┼──────┼───────┼─────────┼───────────────────────────────────────────────┤
    │ Z0  │  -   │  -  │  -   │  -    │   500   │ Zero case – empty inputs                      │
    │ Z1  │  S   │  -  │  A   │ True  │   500   │ Non-zero base, zero exp, empty modulus        │
    │ Z2  │  L   │  -  │  A   │ False │ 32768   │ Large base (1024B), zero exp, empty modulus   │
    │ Z3  │  S   │  -  │  C   │ False |253952   │ Base, large zero exp (1024B), empty modulus   │
    │ Z4  │  S   │  -  │  D   │ False │253952   │ Base, large exp (last byte=1), empty modulus  │
    │ Z5  │  S   │  <  │  A   │ True  │   500   │ Empty base/exp, non-zero modulus only         │
    │ Z6  │  S   │  <  │  B   │ False │  3968   │ Empty base, non-zero exp and modulus          │
    │ Z7  │  L   │  <  │  B   │ False │ 32768   │ Empty base, small exp, large modulus          │
    │ S0  │  S   │  =  │  A   │ True  │   500   │ Small, equal, zero exp, clamped               │
    │ S1  │  S   │  =  │  B   │ True  │   500   │ Small, equal, small exp, clamped              │
    │ S2  │  S   │  =  │  B   │ False │  4080   │ Small, equal, large exp, unclamped            │
    │ S3  │  S   │  =  │  C   │ False │  2048   │ Small, equal, large exp + zero low256         │
    │ S4  │  S   │  =  │  D   │ False │  2048   │ Small, equal, large exp + non-zero low256     │
    │ S5  │  S   │  >  │  A   │ True  │   500   │ Small, base > mod, zero exp, clamped          │
    │ S6  │  S   │  <  │  B   │ True  │   500   │ Small, base < mod, small exp, clamped         │
    │ L0  │  L   │  =  │  A   │ True  │   500   │ Large, equal, zero exp, clamped               │
    │ L1  │  L   │  =  │  B   │ False │ 12750   │ Large, equal, large exp, unclamped            │
    │ L2  │  L   │  =  │  C   │ False │  6400   │ Large, equal, large exp + zero low256         │
    │ L3  │  L   │  =  │  D   │ False │  6400   │ Large, equal, large exp + non-zero low256     │
    │ L4  │  L   │  >  │  B   │ True  │   500   │ Large, base > mod, small exp, clamped         │
    │ L5  │  L   │  <  │  C   │ False │  9216   │ Large, base < mod, large exp + zero low256    │
    │ B1  │  L   │  <  │  B   │ True  │   500   │ Cross 32-byte boundary (31/33)                │
    │ B2  │  L   │  >  │  B   │ True  │   500   │ Cross 32-byte boundary (33/31)                │
    │ B4  │  L   │  =  │  B   │ True  │   500   │ Just over 32-byte boundary                    │
    │ Z8  │  S   │  =  │  A   │ True  │   500   │ All zeros except modulus                      │
    │ Z9  │  S   │  =  │  A   │ True  │   500   │ Zero modulus special case                     │
    │ Z10 │  S   │  =  │  B   │ False │  3968   │ Zero base, large exponent                     │
    │ Z11 │  S   │  =  │  C   │ True  │   500   │ Zero base, 33B zero exp, non-zero modulus     │
    │ Z12 │  S   │  =  │  C   │ False |253952   │ Zero base, large zero exp, non-zero modulus   │
    │ Z13 │  L   │  >  │  A   │ False │ 32768   │ Large zero base, zero exp, non-zero modulus   │
    │ Z14 │  S   │  =  │  C   │ False |253952   │ Base, large zero exp, zero modulus            │
    │ Z15 │  L   │  <  │  B   │ False │ 32768   │ Base, small exp, large zero modulus           │
    │ Z16 │  L   │  <  │  C   │ False │520060928│ Zero base, zero exp, large modulus (gas cap)  |
    │ M1  │  L   │  =  │  D   │ False │ 98176   │ Maximum values stress test                    │
    │ M2  │  S   │  =  │  B   │ True  │   500   │ Max base/mod, small exponent                  │
    │ M3  │  L   │  <  │  D   │ False │ 98176   │ Small base, max exponent/mod                  │
    │ T2  │  S   │  =  │  B   │ True  │   500   │ Tiny maximum values                           │
    │ P2  │  S   │  =  │  B   │ False │  4080   │ High bit in exponent                          │
    │ P3  │  L   │  =  │  D   │ False │  1150   │ Specific bit pattern in large exponent        │
    │ A1  │  L   │  <  │  C   │ False │ 65536   │ Asymmetric: tiny base, large exp/mod          │
    │ A2  │  L   │  >  │  B   │ True  │   500   │ Asymmetric: large base, tiny exp/mod          │
    │ A3  │  L   │  >  │  C   │ False │ 65536   │ Asymmetric: large base/exp, tiny modulus      │
    │ W2  │  S   │  =  │  B   │ True  │   500   │ Exactly 8-byte words                          │
    │ E1  │  S   │  =  │  D   │ True  │   500   │ Exponent exactly 33 bytes                     │
    │ E2  │  S   │  =  │  B   │ False │  4080   │ High bit in exponent first byte               │
    │ E3  │  S   │  =  │  B   │ True  │   500   │ High bit in exponent last byte                │
    │ E4  │  S   │  =  │  B   │ False │  4064   │ Maximum 32-byte exponent                      │
    │ IC1 │  L   │  =  │  B   │ True  │   500   │ Bit shift vs multiplication @ 33 bytes        │
    │ IC3 │  S   │  =  │  B   │ True  │   500   │ Ceiling division at 7 bytes                   │
    │ IC4 │  S   │  =  │  B   │ True  │   500   │ Ceiling division at 9 bytes                   │
    │ IC5 │  S   │  =  │  B   │ False │  2160   │ Bit counting in middle of exponent            │
    │ IC6 │  L   │  =  │  B   │ True  │   500   │ Native library even byte optimization         │
    │ IC7 │  L   │  =  │  B   │ True  │   500   │ Vector optimization 128-bit boundary          │
    │ IC9 │  S   │  =  │  B   │  N/A  │   N/A   │ Zero modulus handling                         │
    │ IC10│  S   │  =  │  B   │ False │  4080   │ Power-of-2 boundary with high bit             │
    └─────┴──────┴─────┴──────┴───────┴─────────┴───────────────────────────────────────────────┘
    """  # noqa: W505
    for base, exponent, modulus, expected_result, gas_usage, test_id in test_cases:
        yield pytest.param(
            ModExpInput(base=base, exponent=exponent, modulus=modulus),
            bytes.fromhex(expected_result),
            gas_usage,
            id=test_id,
        )


@pytest.mark.parametrize(
    "modexp_input,modexp_expected,gas_usage",
    create_modexp_variable_gas_test_cases(),
)
@EIPChecklist.Precompile.Test.InputLengths.Zero()
@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.valid_from("Berlin")
def test_modexp_variable_gas_cost(
    state_test: StateTestFiller,
    precompile_gas: int,
    gas_usage: int,
    pre: Alloc,
    tx: Transaction,
    fork: Fork,
    post: Dict,
) -> None:
    """Test ModExp variable gas cost."""
    if fork >= Osaka:  # Check that gas used defined in table is accurate
        assert (gas_usage is None) or (precompile_gas >= gas_usage), "inconsistent gas usage"
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "modexp_input,modexp_expected,expected_tx_cap_fail",
    [
        pytest.param(
            ModExpInput(base="00" * 32, exponent="00" * 1024, modulus="01" * 1024),
            bytes.fromhex("00" * 1023 + "01"),
            True,
            id="Z16-gas-cap-test",
        ),
    ],
)
@pytest.mark.valid_from("Berlin")
def test_modexp_variable_gas_cost_exceed_tx_gas_cap(
    state_test: StateTestFiller, pre: Alloc, tx: Transaction, post: Dict
) -> None:
    """
    Test ModExp variable gas cost. Inputs with an expected gas cost over the
    EIP-7825 tx gas cap.

    Test case coverage table (gas cap):
    ┌─────┬──────┬─────┬──────┬───────┬─────────┬───────────────────────────────────────────────┐
    │ ID  │ Comp │ Rel │ Iter │ Clamp │   Gas   │ Description                                   │
    ├─────┼──────┼─────┼──────┼───────┼─────────┼───────────────────────────────────────────────┤
    │ Z16 │  L   │  <  │  C   │ False │520060928│ Zero base, zero exp, large modulus (gas cap)  |
    └─────┴──────┴─────┴──────┴───────┴─────────┴───────────────────────────────────────────────┘
    """  # noqa: W505
    state_test(pre=pre, tx=tx, post=post)
