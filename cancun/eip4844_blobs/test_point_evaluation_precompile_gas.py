"""
abstract: Tests gas usage on point evaluation precompile for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)
    Test gas usage on point evaluation precompile for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844).

"""  # noqa: E501

from typing import Dict, Literal

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Environment,
    StateTestFiller,
    Transaction,
    ceiling_division,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .common import INF_POINT, Z
from .spec import Spec, ref_spec_4844

REFERENCE_SPEC_GIT_PATH = ref_spec_4844.git_path
REFERENCE_SPEC_VERSION = ref_spec_4844.version


@pytest.fixture
def precompile_input(proof: Literal["correct", "incorrect"]) -> bytes:
    """Format depending on whether we want a correct proof or not."""
    kzg_commitment = INF_POINT
    kzg_proof = INF_POINT
    z = Z
    # INF_POINT commitment and proof evaluate to 0 on all z values
    y = 0 if proof == "correct" else 1

    versioned_hash = Spec.kzg_to_versioned_hash(kzg_commitment)
    return (
        versioned_hash
        + z.to_bytes(32, "little")
        + y.to_bytes(32, "little")
        + kzg_commitment
        + kzg_proof
    )


@pytest.fixture
def call_type() -> Op:
    """
    Type of call to use to call the precompile.

    Defaults to Op.CALL, but can be parametrized to use other opcode types.
    """
    return Op.CALL


@pytest.fixture
def call_gas() -> int:
    """
    Amount of gas to pass to the precompile.

    Defaults to POINT_EVALUATION_PRECOMPILE_GAS, but can be parametrized to
    test different amounts.
    """
    return Spec.POINT_EVALUATION_PRECOMPILE_GAS


def copy_opcode_cost(fork: Fork, length: int) -> int:
    """
    Calculate the cost of the COPY opcodes, assuming memory expansion from
    empty memory, based on the costs specified in the yellow paper.
    https://ethereum.github.io/yellowpaper/paper.pdf.
    """
    cost_memory_bytes = fork.memory_expansion_gas_calculator()
    return (
        3
        + (ceiling_division(length, 32) * 3)
        + cost_memory_bytes(new_bytes=length, previous_bytes=0)
    )


@pytest.fixture
def precompile_caller_code(
    fork: Fork,
    call_type: Op,
    call_gas: int,
    precompile_input: bytes,
) -> Bytecode:
    """Code to call the point evaluation precompile and evaluate gas usage."""
    calldatasize_cost = 2
    push_operations_cost = 3
    warm_storage_read_cost = 100

    precompile_caller_code = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
    overhead_cost = (
        warm_storage_read_cost
        + (calldatasize_cost * 1)
        + (push_operations_cost * 2)
        + copy_opcode_cost(fork, len(precompile_input))
    )
    if call_type == Op.CALL or call_type == Op.CALLCODE:
        precompile_caller_code += call_type(  # type: ignore # https://github.com/ethereum/execution-spec-tests/issues/348 # noqa: E501
            call_gas,
            Spec.POINT_EVALUATION_PRECOMPILE_ADDRESS,
            0x00,
            0x00,
            Op.CALLDATASIZE,
            0x00,
            0x00,
        )
        overhead_cost += (push_operations_cost * 6) + (calldatasize_cost * 1)
    elif call_type == Op.DELEGATECALL or call_type == Op.STATICCALL:
        # Delegatecall and staticcall use one less argument
        precompile_caller_code += call_type(  # type: ignore # https://github.com/ethereum/execution-spec-tests/issues/348 # noqa: E501
            call_gas,
            Spec.POINT_EVALUATION_PRECOMPILE_ADDRESS,
            0x00,
            Op.CALLDATASIZE,
            0x00,
            0x00,
        )
        overhead_cost += (push_operations_cost * 5) + (calldatasize_cost * 1)

    gas_measure_code = CodeGasMeasure(
        code=precompile_caller_code,
        overhead_cost=overhead_cost,
        extra_stack_items=1,
    )

    return gas_measure_code


@pytest.fixture
def precompile_caller_address(pre: Alloc, precompile_caller_code: Bytecode) -> Address:
    """Address of the precompile caller account."""
    return pre.deploy_contract(precompile_caller_code)


@pytest.fixture
def tx(
    pre: Alloc,
    precompile_caller_address: Address,
    precompile_input: bytes,
) -> Transaction:
    """Prepare transaction used to call the precompile caller account."""
    return Transaction(
        sender=pre.fund_eoa(),
        data=precompile_input,
        to=precompile_caller_address,
        value=0,
        gas_limit=Spec.POINT_EVALUATION_PRECOMPILE_GAS * 20,
    )


@pytest.fixture
def post(
    precompile_caller_address: Address,
    proof: Literal["correct", "incorrect"],
    call_gas: int,
) -> Dict:
    """
    Prepare expected post for each test, depending on the success or
    failure of the precompile call and the gas usage.
    """
    if proof == "correct":
        expected_gas_usage = (
            call_gas
            if call_gas < Spec.POINT_EVALUATION_PRECOMPILE_GAS
            else Spec.POINT_EVALUATION_PRECOMPILE_GAS
        )
    else:
        expected_gas_usage = call_gas
    return {
        precompile_caller_address: Account(
            storage={
                0: expected_gas_usage,
            },
        ),
    }


@pytest.mark.parametrize(
    "call_type",
    [Op.CALL, Op.DELEGATECALL, Op.CALLCODE, Op.STATICCALL],
)
@pytest.mark.parametrize(
    "call_gas",
    [
        Spec.POINT_EVALUATION_PRECOMPILE_GAS,
        Spec.POINT_EVALUATION_PRECOMPILE_GAS - 1,
        Spec.POINT_EVALUATION_PRECOMPILE_GAS + 1,
    ],
    ids=["exact_gas", "insufficient_gas", "extra_gas"],
)
@pytest.mark.parametrize("proof", ["correct", "incorrect"])
@pytest.mark.valid_from("Cancun")
def test_point_evaluation_precompile_gas_usage(
    state_test: StateTestFiller,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Test point evaluation precompile gas usage under different call contexts and gas limits.

    - Test using all call types (CALL, DELEGATECALL, CALLCODE, STATICCALL)
    - Test using different gas limits (exact gas, insufficient gas, extra gas)
    - Test using correct and incorrect proofs
    """
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )
