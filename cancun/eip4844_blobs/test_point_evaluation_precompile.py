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
    - success

    These values correspond to a single call of the precompile, and `success` refers to
    whether the call should succeed or fail.

    All other `pytest.fixture` fixtures can be parametrized to generate new combinations and test
    cases.

"""  # noqa: E501
import glob
import json
import os
from typing import Dict, Iterator, List, Optional

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Block,
    BlockchainTestFiller,
    Environment,
    StateTestFiller,
    Storage,
    TestAddress,
    Transaction,
    eip_2028_transaction_data_cost,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .common import INF_POINT, Z_Y_VALID_ENDIANNESS, Z
from .spec import Spec, ref_spec_4844

REFERENCE_SPEC_GIT_PATH = ref_spec_4844.git_path
REFERENCE_SPEC_VERSION = ref_spec_4844.version


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

    Defaults to Spec.POINT_EVALUATION_PRECOMPILE_GAS, but can be parametrized to
    test different amounts.
    """
    return Spec.POINT_EVALUATION_PRECOMPILE_GAS


@pytest.fixture
def precompile_caller_account(call_type: Op, call_gas: int) -> Account:
    """
    Code to call the point evaluation precompile.
    """
    precompile_caller_code = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
    if call_type == Op.CALL or call_type == Op.CALLCODE:
        precompile_caller_code += Op.SSTORE(
            0,
            call_type(  # type: ignore # https://github.com/ethereum/execution-spec-tests/issues/348 # noqa: E501
                call_gas,
                Spec.POINT_EVALUATION_PRECOMPILE_ADDRESS,
                0x00,
                0x00,
                Op.CALLDATASIZE,
                0x00,
                0x40,
            ),
        )  # Store the result of the precompile call in storage slot 0
    elif call_type == Op.DELEGATECALL or call_type == Op.STATICCALL:
        # Delegatecall and staticcall use one less argument
        precompile_caller_code += Op.SSTORE(
            0,
            call_type(  # type: ignore # https://github.com/ethereum/execution-spec-tests/issues/348 # noqa: E501
                call_gas,
                Spec.POINT_EVALUATION_PRECOMPILE_ADDRESS,
                0x00,
                Op.CALLDATASIZE,
                0x00,
                0x40,
            ),
        )
    precompile_caller_code += (
        # Save the returned values into storage
        Op.SSTORE(1, Op.MLOAD(0x00))
        + Op.SSTORE(2, Op.MLOAD(0x20))
        # Save the returned data length into storage
        + Op.SSTORE(3, Op.RETURNDATASIZE)
        # Save the returned data using RETURNDATACOPY into storage
        + Op.RETURNDATACOPY(0, 0, Op.RETURNDATASIZE)
        + Op.SSTORE(4, Op.MLOAD(0x00))
        + Op.SSTORE(5, Op.MLOAD(0x20))
    )
    return Account(
        nonce=0,
        code=precompile_caller_code,
        balance=0x10**18,
    )


@pytest.fixture
def precompile_caller_address() -> Address:
    """
    Address of the precompile caller account.
    """
    return Address(0x100)


@pytest.fixture
def pre(
    precompile_caller_account: Account,
    precompile_caller_address: Address,
) -> Dict:
    """
    Prepares the pre state of all test cases, by setting the balance of the
    source account of all test transactions, and the precompile caller account.
    """
    return {
        TestAddress: Account(
            nonce=0,
            balance=0x10**18,
        ),
        precompile_caller_address: precompile_caller_account,
    }


@pytest.fixture
def tx(
    precompile_caller_address: Address,
    precompile_input: bytes,
) -> Transaction:
    """
    Prepares transaction used to call the precompile caller account.
    """
    return Transaction(
        ty=2,
        nonce=0,
        data=precompile_input,
        to=precompile_caller_address,
        value=0,
        gas_limit=Spec.POINT_EVALUATION_PRECOMPILE_GAS * 20,
        max_fee_per_gas=7,
        max_priority_fee_per_gas=0,
    )


@pytest.fixture
def post(
    success: bool,
    precompile_caller_address: Address,
    precompile_input: bytes,
) -> Dict:
    """
    Prepares expected post for each test, depending on the success or
    failure of the precompile call.
    """
    expected_storage: Storage.StorageDictType = dict()
    if success:
        # CALL operation success
        expected_storage[0] = 1
        # Success return values
        expected_storage[1] = Spec.FIELD_ELEMENTS_PER_BLOB
        expected_storage[2] = Spec.BLS_MODULUS
        # Success return values size
        expected_storage[3] = 64
        # Success return values from RETURNDATACOPY
        expected_storage[4] = Spec.FIELD_ELEMENTS_PER_BLOB
        expected_storage[5] = Spec.BLS_MODULUS

    else:
        # CALL operation failure
        expected_storage[0] = 0
        # Failure returns zero values
        expected_storage[3] = 0

        # Input parameters were not overwritten since the CALL failed
        expected_storage[1] = precompile_input[0:32]
        expected_storage[2] = precompile_input[32:64]
        expected_storage[4] = expected_storage[1]
        expected_storage[5] = expected_storage[2]
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
@pytest.mark.parametrize("success", [True])
@pytest.mark.valid_from("Cancun")
def test_valid_precompile_calls(
    state_test: StateTestFiller,
    pre: Dict,
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
@pytest.mark.parametrize("success", [False])
@pytest.mark.valid_from("Cancun")
def test_invalid_precompile_calls(
    state_test: StateTestFiller,
    pre: Dict,
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
    if isinstance(data["output"], bool):
        success = data["output"]
    else:
        success = False
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
        success,
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
    "z,y,kzg_commitment,kzg_proof,success",
    all_external_vectors(),
)
@pytest.mark.parametrize("versioned_hash", [None])
@pytest.mark.valid_from("Cancun")
def test_point_evaluation_precompile_external_vectors(
    state_test: StateTestFiller,
    pre: Dict,
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
    "call_gas,y,success",
    [
        (Spec.POINT_EVALUATION_PRECOMPILE_GAS, 0, True),
        (Spec.POINT_EVALUATION_PRECOMPILE_GAS, 1, False),
        (Spec.POINT_EVALUATION_PRECOMPILE_GAS - 1, 0, False),
    ],
    ids=["correct", "incorrect", "insufficient_gas"],
)
@pytest.mark.parametrize(
    "call_type",
    [
        Op.CALL,
        Op.DELEGATECALL,
        Op.CALLCODE,
        Op.STATICCALL,
    ],
)
@pytest.mark.parametrize(
    "z,kzg_commitment,kzg_proof,versioned_hash",
    [[Z, INF_POINT, INF_POINT, None]],
    ids=[""],
)
@pytest.mark.valid_from("Cancun")
def test_point_evaluation_precompile_calls(
    state_test: StateTestFiller,
    pre: Dict,
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
def test_point_evaluation_precompile_gas_tx_to(
    state_test: StateTestFiller,
    precompile_input: bytes,
    call_gas: int,
    proof_correct: bool,
):
    """
    Test calling the Point Evaluation Precompile directly as
    transaction entry point, and measure the gas consumption.

    - Using `gas_limit` with exact necessary gas, insufficient gas and extra gas.
    - Using correct and incorrect proofs
    """
    start_balance = 10**18
    pre = {
        TestAddress: Account(
            nonce=0,
            balance=start_balance,
        ),
    }

    # Gas is appended the intrinsic gas cost of the transaction
    intrinsic_gas_cost = 21_000 + eip_2028_transaction_data_cost(precompile_input)

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
        ty=2,
        nonce=0,
        data=precompile_input,
        to=Address(Spec.POINT_EVALUATION_PRECOMPILE_ADDRESS),
        value=0,
        gas_limit=call_gas + intrinsic_gas_cost,
        max_fee_per_gas=7,
        max_priority_fee_per_gas=0,
    )

    post = {
        TestAddress: Account(
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
@pytest.mark.valid_at_transition_to("Cancun")
def test_point_evaluation_precompile_before_fork(
    state_test: StateTestFiller,
    pre: Dict,
    tx: Transaction,
):
    """
    Test calling the Point Evaluation Precompile before the appropriate fork.
    """
    precompile_caller_code = Op.SSTORE(
        Op.NUMBER,
        Op.CALL(
            Op.GAS,
            Spec.POINT_EVALUATION_PRECOMPILE_ADDRESS,
            1,  # Value
            0,  # Zero-length calldata
            0,
            0,  # Zero-length return
            0,
        ),
    )
    precompile_caller_address = Address(0x100)

    pre = {
        TestAddress: Account(
            nonce=0,
            balance=0x10**18,
        ),
        precompile_caller_address: Account(
            nonce=0,
            code=precompile_caller_code,
            balance=0x10**18,
        ),
    }

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
        tag="point_evaluation_precompile_before_fork",
        pre=pre,
        env=Environment(timestamp=7_500),
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "z,y,kzg_commitment,kzg_proof,versioned_hash",
    [[Z, 0, INF_POINT, INF_POINT, None]],
    ids=["correct_proof"],
)
@pytest.mark.valid_at_transition_to("Cancun")
def test_point_evaluation_precompile_during_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    tx: Transaction,
):
    """
    Test calling the Point Evaluation Precompile before the appropriate fork.
    """
    precompile_caller_code = Op.SSTORE(
        Op.NUMBER,
        Op.CALL(
            Op.GAS,
            Spec.POINT_EVALUATION_PRECOMPILE_ADDRESS,
            1,  # Value
            0,  # Zero-length calldata
            0,
            0,  # Zero-length return
            0,
        ),
    )
    precompile_caller_address = Address(0x100)

    pre = {
        TestAddress: Account(
            nonce=0,
            balance=0x10**18,
        ),
        precompile_caller_address: Account(
            nonce=0,
            code=precompile_caller_code,
            balance=0x10**18,
        ),
    }

    def tx_generator() -> Iterator[Transaction]:
        nonce = 0  # Initial value
        while True:
            yield tx.with_nonce(nonce)
            nonce = nonce + 1

    iter_tx = tx_generator()

    FORK_TIMESTAMP = 15_000
    PRE_FORK_BLOCK_RANGE = range(999, FORK_TIMESTAMP, 1_000)

    # Blocks before fork
    blocks = [Block(timestamp=t, txs=[next(iter_tx)]) for t in PRE_FORK_BLOCK_RANGE]
    # Block after fork
    blocks += [Block(timestamp=FORK_TIMESTAMP, txs=[next(iter_tx)])]

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
        tag="point_evaluation_precompile_before_fork",
        pre=pre,
        post=post,
        blocks=blocks,
    )
