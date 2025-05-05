"""
abstract: Tests minimum gas and input length for BLS12_G1MSM, BLS12_G2MSM, BLS12_PAIRING precompiles of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
    Tests minimum gas and input length for BLS12_G1MSM, BLS12_G2MSM, BLS12_PAIRING precompiles of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537).
"""  # noqa: E501

from typing import List, SupportsBytes

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import Alloc, Bytecode, Environment, StateTestFiller, Storage, Transaction
from ethereum_test_tools import Opcodes as Op

from .spec import GAS_CALCULATION_FUNCTION_MAP, PointG1, PointG2, Scalar, Spec, ref_spec_2537

REFERENCE_SPEC_GIT_PATH = ref_spec_2537.git_path
REFERENCE_SPEC_VERSION = ref_spec_2537.version

pytestmark = pytest.mark.valid_from("Prague")

G1_MSM_K_INPUT_LENGTH = len(PointG1() + Scalar())
G2_MSM_K_INPUT_LENGTH = len(PointG2() + Scalar())
G1_GAS = GAS_CALCULATION_FUNCTION_MAP[Spec.G1MSM]
G2_GAS = GAS_CALCULATION_FUNCTION_MAP[Spec.G2MSM]
PAIRING_GAS = GAS_CALCULATION_FUNCTION_MAP[Spec.PAIRING]
PAIRINGS_TO_TEST = 20


@pytest.fixture
def input_data() -> bytes:
    """Input data for the contract."""
    return b""


@pytest.fixture
def call_contract_code(
    precompile_address: int,
    precompile_gas_list: List[int],
    precompile_data_length_list: List[int],
    expected_output: bytes | SupportsBytes,
    call_opcode: Op,
    call_contract_post_storage: Storage,
) -> Bytecode:
    """
    Code of the test contract to validate minimum expected gas in precompiles, as well as
    expected input lengths on all variable-length input precompiles.

    Code differs from the one used in all other tests in this file, because it accepts a list of
    precompile gas values and a list of precompile data lengths, and for each pair of values, it
    calls the precompile with the given gas and data length, data being passed to the precompile
    is all zeros.

    Args:
        precompile_address:
            Address of the precompile to call.
        precompile_gas_list:
            List of gas values to be used to call the precompile, one for each call.
        precompile_data_length_list:
            List of data lengths to be used to call the precompile, one for each call.
        expected_output:
            Expected output of the contract, it is only used to determine if the call is expected
            to succeed or fail.
        call_opcode:
            Type of call used to call the precompile (Op.CALL, Op.CALLCODE, Op.DELEGATECALL,
            Op.STATICCALL).
        call_contract_post_storage:
            Storage of the test contract after the transaction is executed.

    """
    expected_output = bytes(expected_output)

    # Depending on the expected output, we can deduce if the call is expected to succeed or fail.
    call_succeeds = len(expected_output) > 0

    assert len(precompile_gas_list) == len(precompile_data_length_list)

    assert call_opcode in [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL]
    value = [0] if call_opcode in [Op.CALL, Op.CALLCODE] else []

    code = Bytecode()
    for precompile_gas, precompile_args_length in zip(
        precompile_gas_list, precompile_data_length_list, strict=False
    ):
        # For each given precompile gas value, and given arguments length, call the precompile
        # with the given gas and call data (all zeros) and compare the result.
        code += Op.SSTORE(
            call_contract_post_storage.store_next(1 if call_succeeds else 0),
            Op.CALL(
                precompile_gas,
                precompile_address,
                *value,  # Optional, only used for CALL and CALLCODE.
                0,
                precompile_args_length,  # Memory is empty, so we pass zeros.
                0,
                0,
            ),
        )
    return code


@pytest.fixture
def tx_gas_limit(fork: Fork, input_data: bytes, precompile_gas_list: List[int]) -> int:
    """Transaction gas limit used for the test (Can be overridden in the test)."""
    intrinsic_gas_cost_calculator = fork.transaction_intrinsic_cost_calculator()
    memory_expansion_gas_calculator = fork.memory_expansion_gas_calculator()
    extra_gas = 100_000 * len(precompile_gas_list)
    return (
        extra_gas
        + intrinsic_gas_cost_calculator(calldata=input_data)
        + memory_expansion_gas_calculator(new_bytes=len(input_data))
        + sum(precompile_gas_list)
    )


@pytest.mark.parametrize(
    "precompile_gas_list,precompile_data_length_list",
    [
        pytest.param(
            [G1_GAS(i * G1_MSM_K_INPUT_LENGTH) for i in range(1, len(Spec.G1MSM_DISCOUNT_TABLE))],
            [i * G1_MSM_K_INPUT_LENGTH for i in range(1, len(Spec.G1MSM_DISCOUNT_TABLE))],
            id="exact_gas_full_discount_table",
        ),
        pytest.param(
            [
                G1_GAS(i * G1_MSM_K_INPUT_LENGTH) + 1
                for i in range(1, len(Spec.G1MSM_DISCOUNT_TABLE))
            ],
            [i * G1_MSM_K_INPUT_LENGTH for i in range(1, len(Spec.G1MSM_DISCOUNT_TABLE))],
            id="one_extra_gas_full_discount_table",
        ),
    ],
)
@pytest.mark.parametrize("expected_output", [PointG1()], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G1MSM])
def test_valid_gas_g1msm(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """
    Test the BLS12_G1MSM discount gas table in full, by expecting the call to succeed for
    all possible input lengths because the appropriate amount of gas is provided.

    If any of the calls fail, the test will fail.
    """
    state_test(
        env=Environment(gas_limit=tx.gas_limit),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "precompile_gas_list,precompile_data_length_list",
    [
        pytest.param(
            [0],
            [G1_MSM_K_INPUT_LENGTH],
            id="zero_gas_passed",
        ),
        pytest.param(
            [
                G1_GAS(i * G1_MSM_K_INPUT_LENGTH) - 1
                for i in range(1, len(Spec.G1MSM_DISCOUNT_TABLE))
            ],
            [i * G1_MSM_K_INPUT_LENGTH for i in range(1, len(Spec.G1MSM_DISCOUNT_TABLE))],
            id="insufficient_gas_full_discount_table",
        ),
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G1MSM])
def test_invalid_gas_g1msm(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """
    Test the BLS12_G1MSM discount gas table in full, by expecting the call to fail for
    all possible input lengths because the appropriate amount of gas is not provided.

    If any of the calls succeeds, the test will fail.
    """
    state_test(
        env=Environment(gas_limit=tx.gas_limit),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "precompile_gas_list,precompile_data_length_list",
    [
        pytest.param(
            [G1_GAS(G1_MSM_K_INPUT_LENGTH)],
            [0],
            id="zero_length_input",
        ),
        pytest.param(
            [G1_GAS(i * G1_MSM_K_INPUT_LENGTH) for i in range(1, len(Spec.G1MSM_DISCOUNT_TABLE))],
            [(i * G1_MSM_K_INPUT_LENGTH) - 1 for i in range(1, len(Spec.G1MSM_DISCOUNT_TABLE))],
            id="input_one_byte_too_short_full_discount_table",
        ),
        pytest.param(
            [G1_GAS(i * G1_MSM_K_INPUT_LENGTH) for i in range(1, len(Spec.G1MSM_DISCOUNT_TABLE))],
            [(i * G1_MSM_K_INPUT_LENGTH) + 1 for i in range(1, len(Spec.G1MSM_DISCOUNT_TABLE))],
            id="input_one_byte_too_long_full_discount_table",
        ),
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G1MSM])
def test_invalid_length_g1msm(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """
    Test the BLS12_G1MSM discount gas table in full, by expecting the call to fail for
    all possible input lengths provided because they are too long or short, or zero length.

    If any of the calls succeeds, the test will fail.
    """
    state_test(
        env=Environment(gas_limit=tx.gas_limit),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "precompile_gas_list,precompile_data_length_list",
    [
        pytest.param(
            [G2_GAS(i * G2_MSM_K_INPUT_LENGTH) for i in range(1, len(Spec.G2MSM_DISCOUNT_TABLE))],
            [i * G2_MSM_K_INPUT_LENGTH for i in range(1, len(Spec.G2MSM_DISCOUNT_TABLE))],
            id="exact_gas_full_discount_table",
        ),
        pytest.param(
            [
                G2_GAS(i * G2_MSM_K_INPUT_LENGTH) + 1
                for i in range(1, len(Spec.G2MSM_DISCOUNT_TABLE))
            ],
            [i * G2_MSM_K_INPUT_LENGTH for i in range(1, len(Spec.G2MSM_DISCOUNT_TABLE))],
            id="one_extra_gas_full_discount_table",
        ),
    ],
)
@pytest.mark.parametrize("expected_output", [PointG2()], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G2MSM])
def test_valid_gas_g2msm(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """
    Test the BLS12_G2MSM discount gas table in full, by expecting the call to succeed for
    all possible input lengths because the appropriate amount of gas is provided.

    If any of the calls fail, the test will fail.
    """
    state_test(
        env=Environment(gas_limit=tx.gas_limit),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "precompile_gas_list,precompile_data_length_list",
    [
        pytest.param(
            [0],
            [G2_MSM_K_INPUT_LENGTH],
            id="zero_gas_passed",
        ),
        pytest.param(
            [
                G2_GAS(i * G2_MSM_K_INPUT_LENGTH) - 1
                for i in range(1, len(Spec.G2MSM_DISCOUNT_TABLE))
            ],
            [i * G2_MSM_K_INPUT_LENGTH for i in range(1, len(Spec.G2MSM_DISCOUNT_TABLE))],
            id="insufficient_gas_full_discount_table",
        ),
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G2MSM])
def test_invalid_gas_g2msm(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """
    Test the BLS12_G2MSM discount gas table in full, by expecting the call to fail for
    all possible input lengths because the appropriate amount of gas is not provided.

    If any of the calls succeeds, the test will fail.
    """
    state_test(
        env=Environment(gas_limit=tx.gas_limit),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "precompile_gas_list,precompile_data_length_list",
    [
        pytest.param(
            [G2_GAS(G2_MSM_K_INPUT_LENGTH)],
            [0],
            id="zero_length_input",
        ),
        pytest.param(
            [G2_GAS(i * G2_MSM_K_INPUT_LENGTH) for i in range(1, len(Spec.G2MSM_DISCOUNT_TABLE))],
            [(i * G2_MSM_K_INPUT_LENGTH) - 1 for i in range(1, len(Spec.G2MSM_DISCOUNT_TABLE))],
            id="input_one_byte_too_short_full_discount_table",
        ),
        pytest.param(
            [G2_GAS(i * G2_MSM_K_INPUT_LENGTH) for i in range(1, len(Spec.G2MSM_DISCOUNT_TABLE))],
            [(i * G2_MSM_K_INPUT_LENGTH) + 1 for i in range(1, len(Spec.G2MSM_DISCOUNT_TABLE))],
            id="input_one_byte_too_long_full_discount_table",
        ),
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G2MSM])
def test_invalid_length_g2msm(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """
    Test the BLS12_G2MSM discount gas table in full, by expecting the call to fail for
    all possible input lengths provided because they are too long or short, or zero length.

    If any of the calls succeeds, the test will fail.
    """
    state_test(
        env=Environment(gas_limit=tx.gas_limit),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "precompile_gas_list,precompile_data_length_list",
    [
        pytest.param(
            [PAIRING_GAS(i * Spec.LEN_PER_PAIR) for i in range(1, PAIRINGS_TO_TEST + 1)],
            [i * Spec.LEN_PER_PAIR for i in range(1, PAIRINGS_TO_TEST + 1)],
            id="sufficient_gas",
        ),
        pytest.param(
            [PAIRING_GAS(i * Spec.LEN_PER_PAIR) + 1 for i in range(1, PAIRINGS_TO_TEST + 1)],
            [i * Spec.LEN_PER_PAIR for i in range(1, PAIRINGS_TO_TEST + 1)],
            id="extra_gas",
        ),
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.PAIRING_TRUE], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.PAIRING])
def test_valid_gas_pairing(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """
    Test the BLS12_PAIRING precompile, by expecting the call to succeed for all possible input
    lengths (up to k == PAIRINGS_TO_TEST).

    If any of the calls fails, the test will fail.
    """
    state_test(
        env=Environment(gas_limit=tx.gas_limit),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "precompile_gas_list,precompile_data_length_list",
    [
        pytest.param(
            [0],
            [Spec.LEN_PER_PAIR],
            id="zero_gas_passed",
        ),
        pytest.param(
            [PAIRING_GAS(i * Spec.LEN_PER_PAIR) - 1 for i in range(1, PAIRINGS_TO_TEST + 1)],
            [i * Spec.LEN_PER_PAIR for i in range(1, PAIRINGS_TO_TEST + 1)],
            id="insufficient_gas",
        ),
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.PAIRING])
def test_invalid_gas_pairing(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """
    Test the BLS12_PAIRING precompile, by expecting the call to fail for all possible input
    lengths (up to k == PAIRINGS_TO_TEST) because the appropriate amount of gas is not provided.

    If any of the calls succeeds, the test will fail.
    """
    state_test(
        env=Environment(gas_limit=tx.gas_limit),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "precompile_gas_list,precompile_data_length_list",
    [
        pytest.param(
            [PAIRING_GAS(Spec.LEN_PER_PAIR)],
            [0],
            id="zero_length",
        ),
        pytest.param(
            [PAIRING_GAS(i * Spec.LEN_PER_PAIR) for i in range(1, PAIRINGS_TO_TEST + 1)],
            [(i * Spec.LEN_PER_PAIR) - 1 for i in range(1, PAIRINGS_TO_TEST + 1)],
            id="input_too_short",
        ),
        pytest.param(
            [PAIRING_GAS(i * Spec.LEN_PER_PAIR) for i in range(1, PAIRINGS_TO_TEST + 1)],
            [(i * Spec.LEN_PER_PAIR) + 1 for i in range(1, PAIRINGS_TO_TEST + 1)],
            id="input_too_long",
        ),
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.PAIRING])
def test_invalid_length_pairing(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """
    Test the BLS12_PAIRING precompile, by expecting the call to fail for all possible input
    lengths (up to k == PAIRINGS_TO_TEST) because the incorrect input length was used.

    If any of the calls succeeds, the test will fail.
    """
    state_test(
        env=Environment(gas_limit=tx.gas_limit),
        pre=pre,
        tx=tx,
        post=post,
    )
