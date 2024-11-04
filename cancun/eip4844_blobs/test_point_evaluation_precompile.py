"""
abstract: Tests point evaluation precompile for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)
    Test point evaluation precompile for [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844).

note: Adding a new test
    Add a function that is named `test_<test_name>` and takes at least the following arguments:

    - blockchain_test | state_test
    - pre
    - tx
    - post

    The following arguments *need* to be parametrized or the test will not be generated:

    - versioned_hash
    - kzg_commitment
    - z
    - y
    - kzg_proof
    - result

    These values correspond to a single call of the precompile, and `result` refers to
    whether the call should succeed or fail.

    All other `pytest.fixture` fixtures can be parametrized to generate new combinations and test
    cases.

"""  # noqa: E501
import glob
import json
import os
from enum import Enum
from itertools import count
from typing import Dict, List, Optional

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    EOA,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    StateTestFiller,
    Storage,
    Transaction,
    call_return_code,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .common import INF_POINT, Z_Y_VALID_ENDIANNESS, Z
from .spec import Spec, ref_spec_4844

REFERENCE_SPEC_GIT_PATH = ref_spec_4844.git_path
REFERENCE_SPEC_VERSION = ref_spec_4844.version


class Result(str, Enum):
    """
    Result of the point evaluation precompile.
    """

    SUCCESS = "success"
    FAILURE = "failure"
    OUT_OF_GAS = "out_of_gas"


@pytest.fixture
def precompile_input(
    versioned_hash: Optional[bytes | int],
    kzg_commitment: bytes | int,
    z: bytes | int,
    y: bytes | int,
    kzg_proof: bytes | int,
) -> bytes:
    """
    Format the input for the point evaluation precompile.
    """
    if isinstance(z, int):
        z = z.to_bytes(32, Z_Y_VALID_ENDIANNESS)
    if isinstance(y, int):
        y = y.to_bytes(32, Z_Y_VALID_ENDIANNESS)
    if isinstance(kzg_commitment, int):
        kzg_commitment = kzg_commitment.to_bytes(48, "big")
    if isinstance(kzg_proof, int):
        kzg_proof = kzg_proof.to_bytes(48, "big")
    if versioned_hash is None:
        versioned_hash = Spec.kzg_to_versioned_hash(kzg_commitment)
    elif isinstance(versioned_hash, int):
        versioned_hash = versioned_hash.to_bytes(32, "big")

    return versioned_hash + z + y + kzg_commitment + kzg_proof


@pytest.fixture
def call_opcode() -> Op:
    """
    Type of call to use to call the precompile.

    Defaults to Op.CALL, but can be parametrized to use other opcode types.
    """
    return Op.CALL


@pytest.fixture
def call_gas() -> int:
    """
    Amount of gas to pass to the precompile.

    Defaults to Spec.POINT_EVALUATION_PRECOMPILE_GAS, but can be parametrized to
    test different amounts.
    """
    return Spec.POINT_EVALUATION_PRECOMPILE_GAS


precompile_caller_storage_keys = count()
key_call_return_code = next(precompile_caller_storage_keys)
key_return_1 = next(precompile_caller_storage_keys)
key_return_2 = next(precompile_caller_storage_keys)
key_return_length = next(precompile_caller_storage_keys)
key_return_copy_1 = next(precompile_caller_storage_keys)
key_return_copy_2 = next(precompile_caller_storage_keys)


@pytest.fixture
def precompile_caller_storage() -> Storage.StorageDictType:
    """
    Storage for the precompile caller contract.
    """
    return {
        key_call_return_code: 0xBA5E,
        key_return_1: 0xBA5E,
        key_return_2: 0xBA5E,
        key_return_length: 0xBA5E,
        key_return_copy_1: 0xBA5E,
        key_return_copy_2: 0xBA5E,
    }


@pytest.fixture
def precompile_caller_code(call_opcode: Op, call_gas: int) -> Bytecode:
    """
    Code to call the point evaluation precompile.
    """
    precompile_caller_code = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
    precompile_caller_code += Op.SSTORE(
        key_call_return_code,
        call_opcode(  # type: ignore # https://github.com/ethereum/execution-spec-tests/issues/348 # noqa: E501
            gas=call_gas,
            address=Spec.POINT_EVALUATION_PRECOMPILE_ADDRESS,
            args_offset=0x00,
            args_size=Op.CALLDATASIZE,
            ret_offset=0x00,
            ret_size=0x40,
        ),
    )  # Store the result of the precompile call in storage slot 0
    precompile_caller_code += (
        # Save the returned values into storage
        Op.SSTORE(key_return_1, Op.MLOAD(0x00))
        + Op.SSTORE(key_return_2, Op.MLOAD(0x20))
        # Save the returned data length into storage
        + Op.SSTORE(key_return_length, Op.RETURNDATASIZE)
        # Save the returned data using RETURNDATACOPY into storage
        + Op.RETURNDATACOPY(0, 0, Op.RETURNDATASIZE)
        + Op.SSTORE(key_return_copy_1, Op.MLOAD(0x00))
        + Op.SSTORE(key_return_copy_2, Op.MLOAD(0x20))
        + Op.STOP
    )
    return precompile_caller_code


@pytest.fixture
def precompile_caller_balance() -> int:
    """
    Storage for the precompile caller contract.
    """
    return 0


@pytest.fixture
def precompile_caller_address(
    pre: Alloc,
    precompile_caller_code: Bytecode,
    precompile_caller_storage: Storage.StorageDictType,
    precompile_caller_balance: int,
) -> Address:
    """
    Address of the code to call the point evaluation precompile.
    """
    return pre.deploy_contract(
        precompile_caller_code,
        storage=precompile_caller_storage,
        balance=precompile_caller_balance,
    )


@pytest.fixture
def sender(pre: Alloc) -> EOA:
    """
    Returns the sender account.
    """
    return pre.fund_eoa()


@pytest.fixture
def tx(
    precompile_caller_address: Address,
    precompile_input: bytes,
    sender: EOA,
) -> Transaction:
    """
    Prepares transaction used to call the precompile caller account.
    """
    return Transaction(
        sender=sender,
        data=precompile_input,
        to=precompile_caller_address,
        gas_limit=Spec.POINT_EVALUATION_PRECOMPILE_GAS * 100,
    )


@pytest.fixture
def success(
    result: Result,
    call_opcode: Op,
) -> bool:
    """
    Prepares expected success or failure for each test.
    """
    if call_opcode == Op.EXTDELEGATECALL:
        return False
    if result == Result.OUT_OF_GAS and call_opcode in [Op.EXTCALL, Op.EXTSTATICCALL]:
        return True

    return result == Result.SUCCESS


@pytest.fixture
def post(
    success: bool,
    call_opcode: Op,
    precompile_caller_address: Address,
    precompile_input: bytes,
) -> Dict:
    """
    Prepares expected post for each test, depending on the success or
    failure of the precompile call.
    """
    expected_storage: Storage.StorageDictType = dict()
    # CALL operation return code
    expected_storage[key_call_return_code] = call_return_code(
        call_opcode, success, revert=call_opcode == Op.EXTDELEGATECALL
    )
    if success:
        # Success return values
        expected_storage[key_return_1] = Spec.FIELD_ELEMENTS_PER_BLOB
        expected_storage[key_return_2] = Spec.BLS_MODULUS
        # Success return values size
        expected_storage[key_return_length] = 64
        # Success return values from RETURNDATACOPY
        expected_storage[key_return_copy_1] = Spec.FIELD_ELEMENTS_PER_BLOB
        expected_storage[key_return_copy_2] = Spec.BLS_MODULUS

    else:
        # Failure returns zero values
        expected_storage[key_return_length] = 0

        # Input parameters were not overwritten since the CALL failed
        expected_storage[key_return_1] = precompile_input[0:32]
        expected_storage[key_return_2] = precompile_input[32:64]
        expected_storage[key_return_copy_1] = expected_storage[1]
        expected_storage[key_return_copy_2] = expected_storage[2]
    if call_opcode in [Op.EXTCALL, Op.EXTSTATICCALL, Op.EXTDELEGATECALL]:
        # Input parameters were not overwritten
        expected_storage[key_return_1] = precompile_input[0:32]
        expected_storage[key_return_2] = precompile_input[32:64]
    return {
        precompile_caller_address: Account(
            storage=expected_storage,
        ),
    }


@pytest.mark.parametrize(
    "z,y,kzg_commitment,kzg_proof,versioned_hash",
    [
        pytest.param(Spec.BLS_MODULUS - 1, 0, INF_POINT, INF_POINT, None, id="in_bounds_z"),
    ],
)
@pytest.mark.parametrize("result", [Result.SUCCESS])
@pytest.mark.valid_from("Cancun")
def test_valid_inputs(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
):
    """
    Test valid sanity precompile calls that are expected to succeed.

    - `kzg_commitment` and `kzg_proof` are set to values such that `p(z)==0` for all values of `z`,
    hence `y` is tested to be zero, and call to be successful.
    """
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "z,y,kzg_commitment,kzg_proof,versioned_hash",
    [
        (Spec.BLS_MODULUS, 0, INF_POINT, INF_POINT, None),
        (0, Spec.BLS_MODULUS, INF_POINT, INF_POINT, None),
        (Z, 0, INF_POINT, INF_POINT[:-1], None),
        (Z, 0, INF_POINT, INF_POINT[0:1], None),
        (Z, 0, INF_POINT, INF_POINT + bytes([0]), None),
        (Z, 0, INF_POINT, INF_POINT + bytes([0] * 1023), None),
        (bytes(), bytes(), bytes(), bytes(), bytes()),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, None),
        (Z, 0, INF_POINT, INF_POINT, Spec.kzg_to_versioned_hash(0xC0 << 376, 0x00)),
        (Z, 0, INF_POINT, INF_POINT, Spec.kzg_to_versioned_hash(0xC0 << 376, 0x02)),
        (Z, 0, INF_POINT, INF_POINT, Spec.kzg_to_versioned_hash(0xC0 << 376, 0xFF)),
    ],
    ids=[
        "out_of_bounds_z",
        "out_of_bounds_y",
        "correct_proof_1_input_too_short",
        "correct_proof_1_input_too_short_2",
        "correct_proof_1_input_too_long",
        "correct_proof_1_input_extra_long",
        "null_inputs",
        "zeros_inputs",
        "zeros_inputs_correct_versioned_hash",
        "correct_proof_1_incorrect_versioned_hash_version_0x00",
        "correct_proof_1_incorrect_versioned_hash_version_0x02",
        "correct_proof_1_incorrect_versioned_hash_version_0xff",
    ],
)
@pytest.mark.parametrize("result", [Result.FAILURE])
@pytest.mark.valid_from("Cancun")
def test_invalid_inputs(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
):
    """
    Test invalid precompile calls:

    - Out of bounds inputs `z` and `y`
    - Correct proof, commitment, z and y, but incorrect lengths
    - Null inputs
    - Zero inputs
    - Correct proof, commitment, z and y, but incorrect version versioned hash
    """
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )


def kzg_point_evaluation_vector_from_dict(data: dict):
    """
    Create a KZGPointEvaluation from a dictionary.
    """
    if "input" not in data:
        raise ValueError("Missing 'input' key in data")
    if "output" not in data:
        raise ValueError("Missing 'output' key in data")
    output = data["output"]
    if isinstance(output, bool):
        result = Result.SUCCESS if output else Result.FAILURE
    else:
        result = Result.FAILURE
    input = data["input"]
    if "commitment" not in input or not isinstance(input["commitment"], str):
        raise ValueError("Missing 'commitment' key in data['input']")
    commitment = bytes.fromhex(input["commitment"][2:])
    if "proof" not in input or not isinstance(input["proof"], str):
        raise ValueError("Missing 'proof' key in data['input']")
    proof = bytes.fromhex(input["proof"][2:])
    if "z" not in input or not isinstance(input["z"], str):
        raise ValueError("Missing 'z' key in data['input']")
    z = bytes.fromhex(input["z"][2:])
    if "y" not in input or not isinstance(input["y"], str):
        raise ValueError("Missing 'y' key in data['input']")
    y = bytes.fromhex(input["y"][2:])

    name = data["name"] if "name" in data else ""
    return pytest.param(
        z,
        y,
        commitment,
        proof,
        result,
        id=name,
    )


def load_kzg_point_evaluation_test_vectors_from_file(
    file_path: str,
) -> List:
    """
    Load KZG Point Evaluations from a directory.
    """
    test_vectors = []

    # Load the json file as a dictionary
    with open(file_path, "r") as file:
        data = json.load(file)
        if not isinstance(data, list):
            raise ValueError("Expected a list of point evaluations")
        for item in data:
            if not isinstance(item, dict):
                continue
            test_vectors.append(kzg_point_evaluation_vector_from_dict(item))

    return test_vectors


def current_python_script_directory() -> str:
    """
    Get the current Python script directory.
    """
    return os.path.dirname(os.path.realpath(__file__))


def get_point_evaluation_test_files_in_directory(path: str) -> list[str]:
    """
    Get the point evaluation files in a directory.
    """
    return glob.glob(os.path.join(path, "*.json"))


def all_external_vectors() -> List:
    """
    Tests for the Point Evaluation Precompile from external sources,
    contained in ./point_evaluation_vectors/.
    """
    test_cases = []

    for test_file in get_point_evaluation_test_files_in_directory(
        os.path.join(current_python_script_directory(), "point_evaluation_vectors")
    ):
        file_loaded_tests = load_kzg_point_evaluation_test_vectors_from_file(test_file)
        assert len(file_loaded_tests) > 0
        test_cases += file_loaded_tests

    return test_cases


@pytest.mark.parametrize(
    "z,y,kzg_commitment,kzg_proof,result",
    all_external_vectors(),
)
@pytest.mark.parametrize("versioned_hash", [None])
@pytest.mark.valid_from("Cancun")
def test_external_vectors(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
):
    """
    Test precompile calls using external test vectors compiled from different sources:

    - `go_kzg_4844_verify_kzg_proof.json`: test vectors from the
    [go-kzg-4844](https://github.com/crate-crypto/go-kzg-4844) repository.
    """
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "call_gas,y,result",
    [
        (Spec.POINT_EVALUATION_PRECOMPILE_GAS, 0, Result.SUCCESS),
        (Spec.POINT_EVALUATION_PRECOMPILE_GAS, 1, Result.FAILURE),
        (Spec.POINT_EVALUATION_PRECOMPILE_GAS - 1, 0, Result.OUT_OF_GAS),
    ],
    ids=["correct", "incorrect", "insufficient_gas"],
)
@pytest.mark.with_all_call_opcodes
@pytest.mark.parametrize(
    "z,kzg_commitment,kzg_proof,versioned_hash",
    [[Z, INF_POINT, INF_POINT, None]],
    ids=[""],
)
@pytest.mark.valid_from("Cancun")
def test_call_opcode_types(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    post: Dict,
):
    """
    Test calling the Point Evaluation Precompile with different call types, gas
    and parameter configuration:

    - Using CALL, DELEGATECALL, CALLCODE and STATICCALL.
    - Using correct and incorrect proofs
    - Using barely insufficient gas
    """
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "call_gas",
    [
        (Spec.POINT_EVALUATION_PRECOMPILE_GAS),
        (Spec.POINT_EVALUATION_PRECOMPILE_GAS + 1),
        (Spec.POINT_EVALUATION_PRECOMPILE_GAS - 1),
    ],
    ids=["exact_gas", "extra_gas", "insufficient_gas"],
)
@pytest.mark.parametrize(
    "z,y,kzg_commitment,kzg_proof,versioned_hash,proof_correct",
    [
        [Z, 0, INF_POINT, INF_POINT, None, True],
        [Z, 1, INF_POINT, INF_POINT, None, False],
    ],
    ids=["correct_proof", "incorrect_proof"],
)
@pytest.mark.valid_from("Cancun")
def test_tx_entry_point(
    fork: Fork,
    state_test: StateTestFiller,
    precompile_input: bytes,
    call_gas: int,
    pre: Alloc,
    proof_correct: bool,
):
    """
    Test calling the Point Evaluation Precompile directly as
    transaction entry point, and measure the gas consumption.

    - Using `gas_limit` with exact necessary gas, insufficient gas and extra gas.
    - Using correct and incorrect proofs
    """
    start_balance = 10**18
    sender = pre.fund_eoa(amount=start_balance)

    # Gas is appended the intrinsic gas cost of the transaction
    tx_intrinsic_gas_cost_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas_cost = tx_intrinsic_gas_cost_calculator(calldata=precompile_input)

    # Consumed gas will only be the precompile gas if the proof is correct and
    # the call gas is sufficient.
    # Otherwise, the call gas will be consumed in full.
    consumed_gas = (
        Spec.POINT_EVALUATION_PRECOMPILE_GAS
        if call_gas >= Spec.POINT_EVALUATION_PRECOMPILE_GAS and proof_correct
        else call_gas
    ) + intrinsic_gas_cost

    fee_per_gas = 7

    tx = Transaction(
        sender=sender,
        data=precompile_input,
        to=Address(Spec.POINT_EVALUATION_PRECOMPILE_ADDRESS),
        gas_limit=call_gas + intrinsic_gas_cost,
        gas_price=fee_per_gas,
    )

    post = {
        sender: Account(
            nonce=1,
            balance=start_balance - (consumed_gas * fee_per_gas),
        )
    }

    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "z,y,kzg_commitment,kzg_proof,versioned_hash",
    [[Z, 0, INF_POINT, INF_POINT, None]],
    ids=["correct_proof"],
)
@pytest.mark.parametrize("precompile_caller_storage", [{}], ids=[""])
@pytest.mark.parametrize("precompile_caller_balance", [1], ids=[""])
@pytest.mark.parametrize(
    "precompile_caller_code",
    [
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            Op.NUMBER,
            Op.CALL(
                address=Spec.POINT_EVALUATION_PRECOMPILE_ADDRESS,
                value=1,
                args_size=Op.CALLDATASIZE,
            ),
        )
    ],
    ids=[""],
)
@pytest.mark.valid_at_transition_to("Cancun")
def test_precompile_before_fork(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    precompile_caller_address: Address,
):
    """
    Test calling the Point Evaluation Precompile before the appropriate fork.
    """
    post = {
        precompile_caller_address: Account(
            storage={1: 1},
            # The call succeeds because precompile is not there yet
        ),
        Address(Spec.POINT_EVALUATION_PRECOMPILE_ADDRESS): Account(
            balance=1,
        ),
    }

    state_test(
        pre=pre,
        env=Environment(timestamp=7_500),
        post=post,
        tx=tx,
    )


FORK_TIMESTAMP = 15_000
PRE_FORK_BLOCK_RANGE = range(999, FORK_TIMESTAMP, 1_000)


@pytest.mark.parametrize(
    "z,y,kzg_commitment,kzg_proof,versioned_hash",
    [[Z, 0, INF_POINT, INF_POINT, None]],
    ids=["correct_proof"],
)
@pytest.mark.parametrize("precompile_caller_storage", [{}], ids=[""])
@pytest.mark.parametrize("precompile_caller_balance", [len(PRE_FORK_BLOCK_RANGE)], ids=[""])
@pytest.mark.parametrize(
    "precompile_caller_code",
    [
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            Op.NUMBER,
            Op.CALL(
                address=Spec.POINT_EVALUATION_PRECOMPILE_ADDRESS,
                value=1,
                args_size=Op.CALLDATASIZE,
            ),
        )
    ],
    ids=[""],
)
@pytest.mark.valid_at_transition_to("Cancun")
def test_precompile_during_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    precompile_caller_address: Address,
    precompile_input: bytes,
    sender: EOA,
):
    """
    Test calling the Point Evaluation Precompile before the appropriate fork.
    """
    # Blocks before fork
    blocks = [
        Block(
            timestamp=t,
            txs=[
                Transaction(
                    sender=sender,
                    data=precompile_input,
                    to=precompile_caller_address,
                    gas_limit=Spec.POINT_EVALUATION_PRECOMPILE_GAS * 100,
                )
            ],
        )
        for t in PRE_FORK_BLOCK_RANGE
    ]
    # Block after fork
    blocks += [
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=[
                Transaction(
                    sender=sender,
                    data=precompile_input,
                    to=precompile_caller_address,
                    gas_limit=Spec.POINT_EVALUATION_PRECOMPILE_GAS * 100,
                )
            ],
        )
    ]

    post = {
        precompile_caller_address: Account(
            storage={b: 1 for b in range(1, len(PRE_FORK_BLOCK_RANGE) + 1)},
            # Only the call in the last block's tx fails; storage 0 by default.
        ),
        Address(Spec.POINT_EVALUATION_PRECOMPILE_ADDRESS): Account(
            balance=len(PRE_FORK_BLOCK_RANGE),
        ),
    }

    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
    )
