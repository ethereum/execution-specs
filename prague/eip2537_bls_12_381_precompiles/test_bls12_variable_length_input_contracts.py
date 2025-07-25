"""
abstract: Tests minimum gas and input length for BLS12_G1MSM, BLS12_G2MSM, BLS12_PAIRING precompiles of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
    Tests minimum gas and input length for BLS12_G1MSM, BLS12_G2MSM, BLS12_PAIRING precompiles of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537).
"""  # noqa: E501

from typing import Callable, List, SupportsBytes

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import Alloc, Bytecode, Environment, StateTestFiller, Storage, Transaction
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.utility.pytest import ParameterSet

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
    """Calldata of the transaction is empty because all input in these tests is zero."""
    return b""


@pytest.fixture
def gas_modifier() -> int:
    """Gas modifier to apply to each element of the precompile_gas_list."""
    return 0


@pytest.fixture
def input_length_modifier() -> int:
    """Input length modifier to apply to each element of the precompile_gas_list."""
    return 0


@pytest.fixture
def env(fork: Fork, tx: Transaction) -> Environment:
    """Environment used for all tests."""
    env = Environment()
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    if tx_gas_limit_cap is not None:
        assert tx.gas_limit <= tx_gas_limit_cap, (
            f"tx exceeds gas limit cap: {int(tx.gas_limit)} > {tx_gas_limit_cap}"
        )
    if tx.gas_limit > env.gas_limit:
        env = Environment(gas_limit=tx.gas_limit)
    return env


@pytest.fixture
def call_contract_code(
    precompile_address: int,
    precompile_gas_list: List[int],
    precompile_data_length_list: List[int],
    gas_modifier: int,
    input_length_modifier: int,
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
        gas_modifier:
            Integer to add to the gas passed to the precompile.
        input_length_modifier:
            Integer to add to the length of the input passed to the precompile.
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
                precompile_gas + gas_modifier,
                precompile_address,
                *value,  # Optional, only used for CALL and CALLCODE.
                0,
                precompile_args_length
                + input_length_modifier,  # Memory is empty, so we pass zeros.
                0,
                0,
            ),
        )
    return code


def tx_gas_limit_calculator(
    fork: Fork, precompile_gas_list: List[int], max_precompile_input_length: int
) -> int:
    """Calculate the gas used to execute the transaction with the given precompile gas list."""
    intrinsic_gas_cost_calculator = fork.transaction_intrinsic_cost_calculator()
    memory_expansion_gas_calculator = fork.memory_expansion_gas_calculator()
    extra_gas = 22_500 * len(precompile_gas_list)
    return (
        extra_gas
        + intrinsic_gas_cost_calculator()
        + memory_expansion_gas_calculator(new_bytes=max_precompile_input_length)
        + sum(precompile_gas_list)
    )


@pytest.fixture
def tx_gas_limit(
    fork: Fork,
    input_data: bytes,
    precompile_gas_list: List[int],
    precompile_data_length_list: List[int],
) -> int:
    """Transaction gas limit used for the test (Can be overridden in the test)."""
    assert len(input_data) == 0, "Expected empty data in the transaction."
    return tx_gas_limit_calculator(fork, precompile_gas_list, max(precompile_data_length_list))


def get_split_discount_table_by_fork(
    gas_fn: Callable, discount_table_length: int, element_length: int
) -> Callable[[Fork], List[ParameterSet]]:
    """
    Get the number of test cases needed to cover the given discount table adjusted for the
    fork transaction gas limit cap.

    The function will return the full discount table as a single test case if the
    fork has no transaction gas limit cap, otherwise it will iterate to determine the
    splits required to fit the full discount table across multiple test cases.
    """

    def parametrize_by_fork(fork: Fork) -> List[ParameterSet]:
        tx_gas_limit_cap = fork.transaction_gas_limit_cap()
        if tx_gas_limit_cap is None:
            return [
                pytest.param(
                    [gas_fn(i * element_length) for i in range(1, discount_table_length + 1)],
                    [i * element_length for i in range(1, discount_table_length + 1)],
                    id="full_discount_table",
                )
            ]
        else:

            def gas_list_from_range(min_index: int, max_index: int) -> List[int]:
                return [gas_fn(i * element_length) for i in range(min_index, max_index)]

            def get_range_cost(min_index: int, max_index: int) -> int:
                return tx_gas_limit_calculator(
                    fork,
                    gas_list_from_range(min_index, max_index),
                    max_index * element_length,
                )

            g1_msm_discount_table_ranges = []
            current_min = 1
            for current_max in range(2, discount_table_length + 1):
                range_cost = get_range_cost(current_min, current_max + 1)
                if range_cost > tx_gas_limit_cap:
                    new_range = (current_min, current_max)
                    g1_msm_discount_table_ranges.append(new_range)
                    current_min = current_max
                elif current_max == discount_table_length:
                    new_range = (current_min, current_max + 1)
                    g1_msm_discount_table_ranges.append(new_range)

            g1_msm_discount_table_splits = [
                [
                    [gas_fn(i * element_length) for i in range(r[0], r[1])],
                    [i * element_length for i in range(r[0], r[1])],
                ]
                for r in g1_msm_discount_table_ranges
            ]
            assert (
                sum(len(split[0]) for split in g1_msm_discount_table_splits)
                == discount_table_length
            )
            assert (
                sum(len(split[1]) for split in g1_msm_discount_table_splits)
                == discount_table_length
            )
            return [
                pytest.param(
                    *split,
                    id=f"discount_table_{idx + 1}_of_{len(g1_msm_discount_table_splits)}",
                )
                for idx, split in enumerate(g1_msm_discount_table_splits)
            ]

    return parametrize_by_fork


@pytest.mark.parametrize_by_fork(
    "precompile_gas_list,precompile_data_length_list",
    get_split_discount_table_by_fork(
        G1_GAS, len(Spec.G1MSM_DISCOUNT_TABLE), G1_MSM_K_INPUT_LENGTH
    ),
)
@pytest.mark.parametrize("gas_modifier", [pytest.param(0, id="exact_gas")])
@pytest.mark.parametrize("expected_output", [PointG1()], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G1MSM])
@pytest.mark.slow()
def test_valid_gas_g1msm(
    state_test: StateTestFiller,
    env: Environment,
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
        env=env,
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
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G1MSM])
def test_invalid_zero_gas_g1msm(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_G1MSM precompile calling it with zero gas."""
    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize_by_fork(
    "precompile_gas_list,precompile_data_length_list",
    get_split_discount_table_by_fork(
        G1_GAS, len(Spec.G1MSM_DISCOUNT_TABLE), G1_MSM_K_INPUT_LENGTH
    ),
)
@pytest.mark.parametrize("gas_modifier", [pytest.param(-1, id="insufficient_gas")])
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G1MSM])
def test_invalid_gas_g1msm(
    state_test: StateTestFiller,
    env: Environment,
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
        env=env,
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
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G1MSM])
def test_invalid_zero_length_g1msm(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_G1MSM precompile by passing an input with zero length."""
    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize_by_fork(
    "precompile_gas_list,precompile_data_length_list",
    get_split_discount_table_by_fork(
        G1_GAS, len(Spec.G1MSM_DISCOUNT_TABLE), G1_MSM_K_INPUT_LENGTH
    ),
)
@pytest.mark.parametrize(
    "input_length_modifier",
    [
        pytest.param(-1, id="input_one_byte_too_short"),
        pytest.param(1, id="input_one_byte_too_long"),
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G1MSM])
def test_invalid_length_g1msm(
    state_test: StateTestFiller,
    env: Environment,
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
        env=env,
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize_by_fork(
    "precompile_gas_list,precompile_data_length_list",
    get_split_discount_table_by_fork(
        G2_GAS, len(Spec.G2MSM_DISCOUNT_TABLE), G2_MSM_K_INPUT_LENGTH
    ),
)
@pytest.mark.parametrize("gas_modifier", [pytest.param(0, id="exact_gas")])
@pytest.mark.parametrize("expected_output", [PointG2()], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G2MSM])
@pytest.mark.slow()
def test_valid_gas_g2msm(
    state_test: StateTestFiller,
    env: Environment,
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
        env=env,
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
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G2MSM])
def test_invalid_zero_gas_g2msm(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_G2MSM precompile calling it with zero gas."""
    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize_by_fork(
    "precompile_gas_list,precompile_data_length_list",
    get_split_discount_table_by_fork(
        G2_GAS, len(Spec.G2MSM_DISCOUNT_TABLE), G2_MSM_K_INPUT_LENGTH
    ),
)
@pytest.mark.parametrize("gas_modifier", [pytest.param(-1, id="insufficient_gas")])
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G2MSM])
def test_invalid_gas_g2msm(
    state_test: StateTestFiller,
    env: Environment,
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
        env=env,
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
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G2MSM])
def test_invalid_zero_length_g2msm(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_G2MSM precompile by passing an input with zero length."""
    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize_by_fork(
    "precompile_gas_list,precompile_data_length_list",
    get_split_discount_table_by_fork(
        G2_GAS, len(Spec.G2MSM_DISCOUNT_TABLE), G2_MSM_K_INPUT_LENGTH
    ),
)
@pytest.mark.parametrize(
    "input_length_modifier",
    [
        pytest.param(-1, id="input_one_byte_too_short"),
        pytest.param(1, id="input_one_byte_too_long"),
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.G2MSM])
def test_invalid_length_g2msm(
    state_test: StateTestFiller,
    env: Environment,
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
        env=env,
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize_by_fork(
    "precompile_gas_list,precompile_data_length_list",
    get_split_discount_table_by_fork(PAIRING_GAS, PAIRINGS_TO_TEST, Spec.LEN_PER_PAIR),
)
@pytest.mark.parametrize("gas_modifier", [pytest.param(0, id="exact_gas")])
@pytest.mark.parametrize("expected_output", [Spec.PAIRING_TRUE], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.PAIRING])
def test_valid_gas_pairing(
    state_test: StateTestFiller,
    env: Environment,
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
        env=env,
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
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.PAIRING])
def test_invalid_zero_gas_pairing(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_PAIRING precompile calling it with zero gas."""
    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize_by_fork(
    "precompile_gas_list,precompile_data_length_list",
    get_split_discount_table_by_fork(PAIRING_GAS, PAIRINGS_TO_TEST, Spec.LEN_PER_PAIR),
)
@pytest.mark.parametrize("gas_modifier", [pytest.param(-1, id="insufficient_gas")])
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.PAIRING])
def test_invalid_gas_pairing(
    state_test: StateTestFiller,
    env: Environment,
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
        env=env,
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
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.PAIRING])
def test_invalid_zero_length_pairing(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_PAIRING precompile by passing an input with zero length."""
    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize_by_fork(
    "precompile_gas_list,precompile_data_length_list",
    get_split_discount_table_by_fork(PAIRING_GAS, PAIRINGS_TO_TEST, Spec.LEN_PER_PAIR),
)
@pytest.mark.parametrize(
    "input_length_modifier",
    [
        pytest.param(-1, id="input_one_byte_too_short"),
        pytest.param(1, id="input_one_byte_too_long"),
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
@pytest.mark.parametrize("precompile_address", [Spec.PAIRING])
def test_invalid_length_pairing(
    state_test: StateTestFiller,
    env: Environment,
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
        env=env,
        pre=pre,
        tx=tx,
        post=post,
    )
