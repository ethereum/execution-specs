"""
Test EIP-4844: Shard Blob Transactions (Point Evaulation Precompile)
EIP: https://eips.ethereum.org/EIPS/eip-4844
"""
import glob
import json
import os
from dataclasses import dataclass
from hashlib import sha256
from typing import Dict, Iterator, List, Literal

from ethereum_test_forks import Cancun, Fork, ShanghaiToCancunAtTime15k
from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTest,
    CodeGasMeasure,
    Storage,
    TestAddress,
    Transaction,
    copy_opcode_cost,
    test_from,
    test_only,
    to_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4844.md"
REFERENCE_SPEC_VERSION = "ac003985b9be74ff48bd897770e6d5f2e4318715"

POINT_EVALUATION_PRECOMPILE_ADDRESS = 20
POINT_EVALUATION_PRECOMPILE_GAS = 50_000
BLOB_COMMITMENT_VERSION_KZG = b"\x01"

BLS_MODULUS = (
    0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001
)
BLS_MODULUS_BYTES = BLS_MODULUS.to_bytes(32, "big")
FIELD_ELEMENTS_PER_BLOB = 4096
FIELD_ELEMENTS_PER_BLOB_BYTES = FIELD_ELEMENTS_PER_BLOB.to_bytes(32, "big")


def kzg_to_versioned_hash(
    kzg_commitment: bytes | int,  # 48 bytes
    blob_commitment_version_kzg: bytes | int = BLOB_COMMITMENT_VERSION_KZG,
) -> bytes:
    """
    Calculates the versioned hash for a given KZG commitment.
    """
    if isinstance(kzg_commitment, int):
        kzg_commitment = kzg_commitment.to_bytes(48, "big")
    if isinstance(blob_commitment_version_kzg, int):
        blob_commitment_version_kzg = blob_commitment_version_kzg.to_bytes(
            1, "big"
        )
    return blob_commitment_version_kzg + sha256(kzg_commitment).digest()[1:]


def format_point_evaluation_precompile_input(
    versioned_hash: bytes | int,  # 32 bytes
    z: bytes | int,  # 32 bytes
    y: bytes | int,  # 32 bytes
    kzg_commitment: bytes | int,  # 48 bytes
    kzg_proof: bytes | int,  # 48 bytes
    endianness: Literal["little", "big"] = "big",
) -> bytes:
    """
    Format the input for the point evaluation precompile.
    """
    if isinstance(versioned_hash, int):
        versioned_hash = versioned_hash.to_bytes(32, endianness)
    if isinstance(z, int):
        z = z.to_bytes(32, endianness)
    if isinstance(y, int):
        y = y.to_bytes(32, endianness)
    if isinstance(kzg_commitment, int):
        kzg_commitment = kzg_commitment.to_bytes(48, endianness)
    if isinstance(kzg_proof, int):
        kzg_proof = kzg_proof.to_bytes(48, endianness)

    return versioned_hash + z + y + kzg_commitment + kzg_proof


StorageDictType = Dict[str | int | bytes, str | int | bytes]


@dataclass(kw_only=True)
class KZGPointEvaluation:
    """
    KZG Point Evaluation.
    """

    name: str = ""
    z: bytes | int
    y: bytes | int
    kzg_commitment: bytes | int
    kzg_proof: bytes | int
    versioned_hash: bytes | int | None = None
    endianness: Literal["little", "big"] = "big"
    call_type: Op = Op.CALL
    gas: int = POINT_EVALUATION_PRECOMPILE_GAS
    success: bool

    def get_precompile_input(self) -> bytes:
        """
        Get the input for the point evaluation precompile.
        """
        return format_point_evaluation_precompile_input(
            self.versioned_hash
            if self.versioned_hash is not None
            else kzg_to_versioned_hash(self.kzg_commitment),
            self.z,
            self.y,
            self.kzg_commitment,
            self.kzg_proof,
            self.endianness,
        )

    def generate_blockchain_test(self) -> BlockchainTest:
        """
        Generate BlockchainTest.
        """
        precompile_caller_code = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        if self.call_type == Op.CALL or self.call_type == Op.CALLCODE:
            precompile_caller_code += Op.SSTORE(
                0,
                self.call_type(
                    self.gas,
                    POINT_EVALUATION_PRECOMPILE_ADDRESS,
                    0x00,
                    0x00,
                    Op.CALLDATASIZE,
                    0x00,
                    0x40,
                ),
            )  # Store the result of the precompile call in storage slot 0
        elif (
            self.call_type == Op.DELEGATECALL
            or self.call_type == Op.STATICCALL
        ):
            # Delegatecall and staticcall use one less argument
            precompile_caller_code += Op.SSTORE(
                0,
                self.call_type(
                    self.gas,
                    POINT_EVALUATION_PRECOMPILE_ADDRESS,
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

        precompile_caller_address = to_address(0x100)

        pre = {
            TestAddress: Account(
                nonce=0,
                balance=0x10**18,
            ),
            precompile_caller_address: Account(
                nonce=0,
                code=precompile_caller_code,
            ),
        }

        precompile_calldata = self.get_precompile_input()
        tx = Transaction(
            ty=2,
            nonce=0,
            data=precompile_calldata,
            to=precompile_caller_address,
            value=0,
            gas_limit=POINT_EVALUATION_PRECOMPILE_GAS * 20,
            max_fee_per_gas=7,
            max_priority_fee_per_gas=0,
        )

        expected_storage: Storage.StorageDictType = dict()
        if self.success:
            # CALL operation success
            expected_storage[0] = 1
            # Success return values
            expected_storage[1] = FIELD_ELEMENTS_PER_BLOB
            expected_storage[2] = BLS_MODULUS
            # Success return values size
            expected_storage[3] = 64
            # Success return values from RETURNDATACOPY
            expected_storage[4] = FIELD_ELEMENTS_PER_BLOB
            expected_storage[5] = BLS_MODULUS

        else:
            # CALL operation failure
            expected_storage[0] = 0
            # Failure returns zero values
            expected_storage[3] = 0

            # Input parameters were not overwritten since the CALL failed
            expected_storage[1] = precompile_calldata[0:32]
            expected_storage[2] = precompile_calldata[32:64]
            expected_storage[4] = expected_storage[1]
            expected_storage[5] = expected_storage[2]

        post = {
            precompile_caller_address: Account(
                storage=expected_storage,
            ),
        }

        return BlockchainTest(
            tag=self.name,
            pre=pre,
            post=post,
            blocks=[Block(txs=[tx])],
        )

    def generate_gas_test(self, expected_gas_usage: int) -> BlockchainTest:
        """
        Generate BlockchainTest to measure precompile gas usage.
        """
        CALLDATASIZE_COST = 2
        PUSH_OPERATIONS_COST = 3
        WARM_STORAGE_READ_COST = 100
        precompile_calldata = self.get_precompile_input()

        precompile_caller_code = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        overhead_cost = (
            WARM_STORAGE_READ_COST
            + (CALLDATASIZE_COST * 1)
            + (PUSH_OPERATIONS_COST * 2)
            + copy_opcode_cost(len(precompile_calldata))
        )
        if self.call_type == Op.CALL or self.call_type == Op.CALLCODE:
            precompile_caller_code += self.call_type(
                self.gas,
                POINT_EVALUATION_PRECOMPILE_ADDRESS,
                0x00,
                0x00,
                Op.CALLDATASIZE,
                0x00,
                0x00,
            )
            overhead_cost += (PUSH_OPERATIONS_COST * 6) + (
                CALLDATASIZE_COST * 1
            )
        elif (
            self.call_type == Op.DELEGATECALL
            or self.call_type == Op.STATICCALL
        ):
            # Delegatecall and staticcall use one less argument
            precompile_caller_code += self.call_type(
                self.gas,
                POINT_EVALUATION_PRECOMPILE_ADDRESS,
                0x00,
                Op.CALLDATASIZE,
                0x00,
                0x00,
            )
            overhead_cost += (PUSH_OPERATIONS_COST * 5) + (
                CALLDATASIZE_COST * 1
            )

        gas_measure_code = CodeGasMeasure(
            code=precompile_caller_code,
            overhead_cost=overhead_cost,
            extra_stack_items=1,
        )

        precompile_caller_address = to_address(0x100)

        pre = {
            TestAddress: Account(
                nonce=0,
                balance=0x10**18,
            ),
            precompile_caller_address: Account(
                nonce=0,
                code=gas_measure_code,
            ),
        }

        tx = Transaction(
            ty=2,
            nonce=0,
            data=precompile_calldata,
            to=precompile_caller_address,
            value=0,
            gas_limit=POINT_EVALUATION_PRECOMPILE_GAS * 20,
            max_fee_per_gas=7,
            max_priority_fee_per_gas=0,
        )

        post = {
            precompile_caller_address: Account(
                storage={
                    0: expected_gas_usage,
                },
            ),
        }

        return BlockchainTest(
            tag=self.name,
            pre=pre,
            post=post,
            blocks=[Block(txs=[tx])],
        )

    @classmethod
    def from_dict(cls, data: dict) -> "KZGPointEvaluation":
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
        if "commitment" not in input or not isinstance(
            input["commitment"], str
        ):
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
        return cls(
            name=name,
            z=z,
            y=y,
            kzg_commitment=commitment,
            kzg_proof=proof,
            success=success,
        )


def load_kzg_point_evaluation_test_vectors_from_file(
    file_path: str,
) -> list[KZGPointEvaluation]:
    """
    Load KZG Point Evaluations from a directory.
    """
    test_vectors: list[KZGPointEvaluation] = []

    # Load the json file as a dictionary
    with open(file_path, "r") as file:
        data = json.load(file)
        if not isinstance(data, list):
            raise ValueError("Expected a list of point evaluations")
        for item in data:
            if not isinstance(item, dict):
                continue
            test_vectors.append(KZGPointEvaluation.from_dict(item))

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


@test_from(fork=Cancun)
def test_point_evaluation_precompile(_: Fork):
    """
    Tests for the Point Evaluation Precompile.
    Verify p(z) = y given commitment that corresponds to the polynomial p(x)
    and a KZG proof.
    Also verify that the provided commitment matches the provided
    versioned_hash.
    """
    z = 0x623CE31CF9759A5C8DAF3A357992F9F3DD7F9339D8998BC8E68373E54F00B75E
    test_cases: List[KZGPointEvaluation] = [
        KZGPointEvaluation(
            name="out_of_bounds_z",
            z=BLS_MODULUS,
            y=0,
            kzg_commitment=0,
            kzg_proof=0,
            success=False,
        ),
        KZGPointEvaluation(
            name="out_of_bounds_y",
            z=0,
            y=BLS_MODULUS,
            kzg_commitment=0,
            kzg_proof=0,
            success=False,
        ),
        KZGPointEvaluation(
            name="correct_proof_1",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=0xC0 << 376,
            success=True,
        ),
        KZGPointEvaluation(
            name="correct_proof_1_input_too_short",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=bytes([0xC0] + [0] * 46),
            versioned_hash=kzg_to_versioned_hash(0xC0 << 376),
            success=False,
        ),
        KZGPointEvaluation(
            name="correct_proof_1_input_too_short_2",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=bytes([0xC0]),
            versioned_hash=kzg_to_versioned_hash(0xC0 << 376),
            success=False,
        ),
        KZGPointEvaluation(
            name="correct_proof_1_input_too_long",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=bytes([0xC0] + [0] * 48),
            versioned_hash=kzg_to_versioned_hash(0xC0 << 376),
            success=False,
        ),
        KZGPointEvaluation(
            name="correct_proof_1_input_extra_long",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=bytes([0xC0] + [0] * 1024),
            versioned_hash=kzg_to_versioned_hash(0xC0 << 376),
            success=False,
        ),
        KZGPointEvaluation(
            name="null_inputs",
            z=bytes(),
            y=bytes(),
            kzg_commitment=bytes(),
            kzg_proof=bytes(),
            versioned_hash=bytes(),
            success=False,
        ),
        KZGPointEvaluation(
            name="zeros_inputs",
            z=0,
            y=0,
            kzg_commitment=0,
            kzg_proof=0,
            versioned_hash=0,
            success=False,
        ),
        KZGPointEvaluation(
            name="zeros_inputs_correct_versioned_hash",
            z=0,
            y=0,
            kzg_commitment=0,
            kzg_proof=0,
            success=False,
        ),
        KZGPointEvaluation(
            name="correct_proof_1_inverted_endianness",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=0xC0 << 376,
            success=False,
            endianness="little",
        ),
        KZGPointEvaluation(
            name="correct_proof_1_incorrect_versioned_hash_version_0x00",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=0xC0 << 376,
            versioned_hash=kzg_to_versioned_hash(
                0xC0 << 376,
                0x00,
            ),
            success=False,
        ),
        KZGPointEvaluation(
            name="correct_proof_1_incorrect_versioned_hash_version_0x02",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=0xC0 << 376,
            versioned_hash=kzg_to_versioned_hash(
                0xC0 << 376,
                0x02,
            ),
            success=False,
        ),
        KZGPointEvaluation(
            name="correct_proof_1_incorrect_versioned_hash_version_0xff",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=0xC0 << 376,
            versioned_hash=kzg_to_versioned_hash(
                0xC0 << 376,
                0xFF,
            ),
            success=False,
        ),
    ]

    # Rest are loaded from the YAML files
    for test_file in get_point_evaluation_test_files_in_directory(
        os.path.join(
            current_python_script_directory(), "point_evaluation_vectors"
        )
    ):
        file_loaded_tests = load_kzg_point_evaluation_test_vectors_from_file(
            test_file
        )
        assert len(file_loaded_tests) > 0
        test_cases += file_loaded_tests

    for test_case in test_cases:
        yield test_case.generate_blockchain_test()


@test_from(fork=Cancun)
def test_point_evaluation_precompile_calls(_: Fork):
    """
    Test calling the Point Evaluation Precompile with different call types, gas
    and parameter configuration.
    """
    z = 0x623CE31CF9759A5C8DAF3A357992F9F3DD7F9339D8998BC8E68373E54F00B75E

    # Call
    yield KZGPointEvaluation(
        name="call_insufficient_gas",
        z=z,
        y=0,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        gas=POINT_EVALUATION_PRECOMPILE_GAS - 1,
        success=False,
    ).generate_blockchain_test()

    # Delegatecall
    yield KZGPointEvaluation(
        name="delegatecall_correct",
        z=z,
        y=0,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        call_type=Op.DELEGATECALL,
        success=True,
    ).generate_blockchain_test()
    yield KZGPointEvaluation(
        name="delegatecall_incorrect",
        z=z,
        y=1,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        call_type=Op.DELEGATECALL,
        success=False,
    ).generate_blockchain_test()
    yield KZGPointEvaluation(
        name="delegatecall_insufficient_gas",
        z=z,
        y=0,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        gas=POINT_EVALUATION_PRECOMPILE_GAS - 1,
        call_type=Op.DELEGATECALL,
        success=False,
    ).generate_blockchain_test()

    # Callcode
    yield KZGPointEvaluation(
        name="callcode_correct",
        z=z,
        y=0,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        call_type=Op.CALLCODE,
        success=True,
    ).generate_blockchain_test()
    yield KZGPointEvaluation(
        name="callcode_incorrect",
        z=z,
        y=1,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        call_type=Op.CALLCODE,
        success=False,
    ).generate_blockchain_test()
    yield KZGPointEvaluation(
        name="callcode_insufficient_gas",
        z=z,
        y=0,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        gas=POINT_EVALUATION_PRECOMPILE_GAS - 1,
        call_type=Op.CALLCODE,
        success=False,
    ).generate_blockchain_test()

    # Staticcall
    yield KZGPointEvaluation(
        name="staticcall_correct",
        z=z,
        y=0,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        call_type=Op.STATICCALL,
        success=True,
    ).generate_blockchain_test()
    yield KZGPointEvaluation(
        name="staticcall_incorrect",
        z=z,
        y=1,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        call_type=Op.STATICCALL,
        success=False,
    ).generate_blockchain_test()
    yield KZGPointEvaluation(
        name="staticcall_insufficient_gas",
        z=z,
        y=0,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        gas=POINT_EVALUATION_PRECOMPILE_GAS - 1,
        call_type=Op.STATICCALL,
        success=False,
    ).generate_blockchain_test()


@test_from(fork=Cancun)
def test_point_evaluation_precompile_gas_usage(_: Fork):
    """
    Test Precompile Gas Usage.
    """
    z = 0x623CE31CF9759A5C8DAF3A357992F9F3DD7F9339D8998BC8E68373E54F00B75E
    call_types = [Op.CALL, Op.DELEGATECALL, Op.CALLCODE, Op.STATICCALL]
    for call_type in call_types:
        yield KZGPointEvaluation(
            name=f"{call_type}_correct_proof_sufficient_gas",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=0xC0 << 376,
            gas=POINT_EVALUATION_PRECOMPILE_GAS,
            success=True,
        ).generate_gas_test(expected_gas_usage=POINT_EVALUATION_PRECOMPILE_GAS)
        yield KZGPointEvaluation(
            name=f"{call_type}_incorrect_proof_sufficient_gas",
            z=z,
            y=1,
            kzg_commitment=0xC0 << 376,
            kzg_proof=0xC0 << 376,
            gas=POINT_EVALUATION_PRECOMPILE_GAS,
            success=False,
        ).generate_gas_test(expected_gas_usage=POINT_EVALUATION_PRECOMPILE_GAS)
        yield KZGPointEvaluation(
            name=f"{call_type}_correct_proof_extra_gas",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=0xC0 << 376,
            gas=POINT_EVALUATION_PRECOMPILE_GAS + 1,
            success=True,
        ).generate_gas_test(expected_gas_usage=POINT_EVALUATION_PRECOMPILE_GAS)
        yield KZGPointEvaluation(
            name=f"{call_type}_incorrect_proof_extra_gas",
            z=z,
            y=1,
            kzg_commitment=0xC0 << 376,
            kzg_proof=0xC0 << 376,
            gas=POINT_EVALUATION_PRECOMPILE_GAS + 1,
            success=True,
        ).generate_gas_test(
            expected_gas_usage=POINT_EVALUATION_PRECOMPILE_GAS + 1
        )
        yield KZGPointEvaluation(
            name=f"{call_type}_correct_proof_insufficient_gas",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=0xC0 << 376,
            gas=POINT_EVALUATION_PRECOMPILE_GAS - 1,
            success=False,
        ).generate_gas_test(
            expected_gas_usage=POINT_EVALUATION_PRECOMPILE_GAS - 1
        )


@test_only(fork=ShanghaiToCancunAtTime15k)
def test_point_evaluation_precompile_before_fork(_: Fork):
    """
    Test calling the Point Evaluation Precompile before the appropriate fork.
    """
    precompile_caller_code = Op.SSTORE(
        Op.NUMBER,
        Op.CALL(
            Op.GAS,
            POINT_EVALUATION_PRECOMPILE_ADDRESS,
            1,  # Value
            0,  # Zero-length calldata
            0,
            0,  # Zero-length return
            0,
        ),
    )
    precompile_caller_address = to_address(0x100)

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
            tx = Transaction(
                ty=2,
                nonce=nonce,
                to=precompile_caller_address,
                value=0,
                gas_limit=POINT_EVALUATION_PRECOMPILE_GAS * 10,
                max_fee_per_gas=7,
                max_priority_fee_per_gas=0,
            )
            nonce = nonce + 1
            yield tx

    iter_tx = tx_generator()

    FORK_TIMESTAMP = 15_000
    PRE_FORK_BLOCK_RANGE = range(999, FORK_TIMESTAMP, 1_000)

    # Blocks before fork
    blocks = [
        Block(timestamp=t, txs=[next(iter_tx)]) for t in PRE_FORK_BLOCK_RANGE
    ]
    # Block after fork
    blocks += [Block(timestamp=FORK_TIMESTAMP, txs=[next(iter_tx)])]

    post = {
        precompile_caller_address: Account(
            storage={b: 1 for b in range(1, len(PRE_FORK_BLOCK_RANGE) + 1)},
        ),
        to_address(POINT_EVALUATION_PRECOMPILE_ADDRESS): Account(
            balance=len(PRE_FORK_BLOCK_RANGE),
        ),
    }

    yield BlockchainTest(
        tag="point_evaluation_precompile_before_fork",
        pre=pre,
        post=post,
        blocks=blocks,
    )
