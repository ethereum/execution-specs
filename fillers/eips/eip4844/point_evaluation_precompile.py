"""
Test EIP-4844: Shard Blob Transactions (Point Evaulation Precompile)
EIP: https://eips.ethereum.org/EIPS/eip-4844
"""
import glob
import json
import os
from dataclasses import dataclass
from hashlib import sha256
from typing import Iterator, List, Literal

from ethereum_test_forks import Cancun, Fork, ShanghaiToCancunAtTime15k
from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTest,
    TestAddress,
    Transaction,
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
    gas: int = POINT_EVALUATION_PRECOMPILE_ADDRESS
    correct: bool

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
        precompile_caller_code += Op.SSTORE(1, Op.MLOAD(0x00))
        precompile_caller_code += Op.SSTORE(2, Op.MLOAD(0x20))
        precompile_caller_code += Op.SSTORE(3, Op.RETURNDATASIZE)
        precompile_caller_code += Op.RETURNDATACOPY(0, 0, Op.RETURNDATASIZE)
        precompile_caller_code += Op.SSTORE(4, Op.MLOAD(0x00))
        precompile_caller_code += Op.SSTORE(5, Op.MLOAD(0x20))

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
            gas_limit=POINT_EVALUATION_PRECOMPILE_GAS * 10,
            max_fee_per_gas=7,
            max_priority_fee_per_gas=0,
        )

        expected_storage = {}
        if self.correct:
            expected_storage[0] = 1
            expected_storage[1] = FIELD_ELEMENTS_PER_BLOB
            expected_storage[2] = BLS_MODULUS
            expected_storage[3] = 64
            expected_storage[4] = FIELD_ELEMENTS_PER_BLOB
            expected_storage[5] = BLS_MODULUS

        else:
            expected_storage[0] = 0
            expected_storage[3] = 0
            expected_storage[4] = 0
            expected_storage[5] = 0

            if self.gas >= POINT_EVALUATION_PRECOMPILE_GAS:
                # The call will execute, and overwrite the memory at 0,
                # even if the kzg proof is invalid or malformed.
                expected_storage[1] = 0
                expected_storage[2] = 0
            else:
                # If the gas is insufficient, the call won't even be executed
                # and therefore the memory at 0 won't be overwritten, leaving
                # the original parameters untouched.
                expected_storage[1] = precompile_calldata[0:32]
                expected_storage[2] = precompile_calldata[32:64]

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
            correct = data["output"]
        else:
            correct = False
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
            correct=correct,
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


# @test_from(fork=Cancun)
def test_point_evaluation_precompile_gas_usage(_: Fork):
    """
    Test Precompile Gas Usage.
    """


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
            correct=False,
        ),
        KZGPointEvaluation(
            name="out_of_bounds_y",
            z=0,
            y=BLS_MODULUS,
            kzg_commitment=0,
            kzg_proof=0,
            correct=False,
        ),
        KZGPointEvaluation(
            name="correct_proof_1",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=0xC0 << 376,
            correct=True,
        ),
        KZGPointEvaluation(
            name="correct_proof_1_input_too_short",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=bytes([0xC0] + [0] * 46),
            versioned_hash=kzg_to_versioned_hash(0xC0 << 376),
            correct=False,
        ),
        KZGPointEvaluation(
            name="correct_proof_1_input_too_short_2",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=bytes([0xC0]),
            versioned_hash=kzg_to_versioned_hash(0xC0 << 376),
            correct=False,
        ),
        KZGPointEvaluation(
            name="correct_proof_1_input_too_long",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=bytes([0xC0] + [0] * 48),
            versioned_hash=kzg_to_versioned_hash(0xC0 << 376),
            correct=False,
        ),
        KZGPointEvaluation(
            name="correct_proof_1_input_extra_long",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=bytes([0xC0] + [0] * 1024),
            versioned_hash=kzg_to_versioned_hash(0xC0 << 376),
            correct=False,
        ),
        KZGPointEvaluation(
            name="null_inputs",
            z=bytes(),
            y=bytes(),
            kzg_commitment=bytes(),
            kzg_proof=bytes(),
            versioned_hash=bytes(),
            correct=False,
        ),
        KZGPointEvaluation(
            name="zeros_inputs",
            z=0,
            y=0,
            kzg_commitment=0,
            kzg_proof=0,
            versioned_hash=0,
            correct=False,
        ),
        KZGPointEvaluation(
            name="zeros_inputs_correct_versioned_hash",
            z=0,
            y=0,
            kzg_commitment=0,
            kzg_proof=0,
            correct=False,
        ),
        KZGPointEvaluation(
            name="correct_proof_1_inverted_endianness",
            z=z,
            y=0,
            kzg_commitment=0xC0 << 376,
            kzg_proof=0xC0 << 376,
            correct=False,
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
            correct=False,
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
            correct=False,
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
            correct=False,
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

    # Delegatecall
    yield KZGPointEvaluation(
        name="delegatecall_correct",
        z=z,
        y=0,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        call_type=Op.DELEGATECALL,
        correct=True,
    ).generate_blockchain_test()
    yield KZGPointEvaluation(
        name="delegatecall_incorrect",
        z=z,
        y=1,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        call_type=Op.DELEGATECALL,
        correct=False,
    ).generate_blockchain_test()

    # Callcode
    yield KZGPointEvaluation(
        name="callcode_correct",
        z=z,
        y=0,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        call_type=Op.CALLCODE,
        correct=True,
    ).generate_blockchain_test()
    yield KZGPointEvaluation(
        name="callcode_incorrect",
        z=z,
        y=1,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        call_type=Op.CALLCODE,
        correct=False,
    ).generate_blockchain_test()

    # Staticcall
    yield KZGPointEvaluation(
        name="staticcall_correct",
        z=z,
        y=0,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        call_type=Op.STATICCALL,
        correct=True,
    ).generate_blockchain_test()
    yield KZGPointEvaluation(
        name="staticcall_incorrect",
        z=z,
        y=1,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        call_type=Op.STATICCALL,
        correct=False,
    ).generate_blockchain_test()

    # Gas
    yield KZGPointEvaluation(
        name="sufficient_gas",
        z=z,
        y=0,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        gas=POINT_EVALUATION_PRECOMPILE_GAS,
        correct=True,
    ).generate_blockchain_test()
    yield KZGPointEvaluation(
        name="insufficient_gas",
        z=z,
        y=0,
        kzg_commitment=0xC0 << 376,
        kzg_proof=0xC0 << 376,
        gas=POINT_EVALUATION_PRECOMPILE_GAS - 1,
        correct=True,
    ).generate_blockchain_test()


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
