"""
All Ethereum fork class definitions.
"""

from hashlib import sha256
from os.path import realpath
from pathlib import Path
from typing import List, Mapping, Optional, Tuple

from semver import Version

from ethereum_test_base_types import Address
from ethereum_test_vm import EVMCodeType, Opcodes

from ..base_fork import BaseFork

CURRENT_FILE = Path(realpath(__file__))
CURRENT_FOLDER = CURRENT_FILE.parent


# All forks must be listed here !!! in the order they were introduced !!!
class Frontier(BaseFork, solc_name="homestead"):
    """
    Frontier fork
    """

    @classmethod
    def transition_tool_name(cls, block_number: int = 0, timestamp: int = 0) -> str:
        """
        Returns fork name as it's meant to be passed to the transition tool for execution.
        """
        if cls._transition_tool_name is not None:
            return cls._transition_tool_name
        return cls.name()

    @classmethod
    def solc_name(cls) -> str:
        """
        Returns fork name as it's meant to be passed to the solc compiler.
        """
        if cls._solc_name is not None:
            return cls._solc_name
        return cls.name().lower()

    @classmethod
    def solc_min_version(cls) -> Version:
        """
        Returns the minimum version of solc that supports this fork.
        """
        return Version.parse("0.8.20")

    @classmethod
    def header_base_fee_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        At genesis, header must not contain base fee
        """
        return False

    @classmethod
    def header_prev_randao_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        At genesis, header must not contain Prev Randao value
        """
        return False

    @classmethod
    def header_zero_difficulty_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        At genesis, header must not have difficulty zero
        """
        return False

    @classmethod
    def header_withdrawals_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        At genesis, header must not contain withdrawals
        """
        return False

    @classmethod
    def header_excess_blob_gas_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        At genesis, header must not contain excess blob gas
        """
        return False

    @classmethod
    def header_blob_gas_used_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        At genesis, header must not contain blob gas used
        """
        return False

    @classmethod
    def blob_gas_per_blob(cls, block_number: int, timestamp: int) -> int:
        """
        Returns the amount of blob gas used per blob for a given fork.
        """
        return 0

    @classmethod
    def header_requests_required(cls, block_number: int, timestamp: int) -> bool:
        """
        At genesis, header must not contain beacon chain requests.
        """
        return False

    @classmethod
    def engine_new_payload_version(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """
        At genesis, payloads cannot be sent through the engine API
        """
        return None

    @classmethod
    def header_beacon_root_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        At genesis, header must not contain parent beacon block root
        """
        return False

    @classmethod
    def engine_new_payload_blob_hashes(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        At genesis, payloads do not have blob hashes.
        """
        return False

    @classmethod
    def engine_new_payload_beacon_root(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        At genesis, payloads do not have a parent beacon block root.
        """
        return False

    @classmethod
    def engine_forkchoice_updated_version(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """
        At genesis, forkchoice updates cannot be sent through the engine API.
        """
        return cls.engine_new_payload_version(block_number, timestamp)

    @classmethod
    def get_reward(cls, block_number: int = 0, timestamp: int = 0) -> int:
        """
        At Genesis the expected reward amount in wei is
        5_000_000_000_000_000_000
        """
        return 5_000_000_000_000_000_000

    @classmethod
    def tx_types(cls, block_number: int = 0, timestamp: int = 0) -> List[int]:
        """
        At Genesis, only legacy transactions are allowed
        """
        return [0]

    @classmethod
    def contract_creating_tx_types(cls, block_number: int = 0, timestamp: int = 0) -> List[int]:
        """
        At Genesis, only legacy transactions are allowed
        """
        return [0]

    @classmethod
    def precompiles(cls, block_number: int = 0, timestamp: int = 0) -> List[Address]:
        """
        At Genesis, no pre-compiles are present
        """
        return []

    @classmethod
    def system_contracts(cls, block_number: int = 0, timestamp: int = 0) -> List[Address]:
        """
        At Genesis, no system-contracts are present
        """
        return []

    @classmethod
    def evm_code_types(cls, block_number: int = 0, timestamp: int = 0) -> List[EVMCodeType]:
        """
        At Genesis, only legacy EVM code is supported.
        """
        return [EVMCodeType.LEGACY]

    @classmethod
    def call_opcodes(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> List[Tuple[Opcodes, EVMCodeType]]:
        """
        Returns the list of call opcodes supported by the fork.
        """
        return [
            (Opcodes.CALL, EVMCodeType.LEGACY),
            (Opcodes.CALLCODE, EVMCodeType.LEGACY),
        ]

    @classmethod
    def valid_opcodes(
        cls,
    ) -> List[Opcodes]:
        """
        Returns the list of Opcodes that are valid to work on this fork.
        """
        return [
            Opcodes.STOP,
            Opcodes.ADD,
            Opcodes.MUL,
            Opcodes.SUB,
            Opcodes.DIV,
            Opcodes.SDIV,
            Opcodes.MOD,
            Opcodes.SMOD,
            Opcodes.ADDMOD,
            Opcodes.MULMOD,
            Opcodes.EXP,
            Opcodes.SIGNEXTEND,
            Opcodes.LT,
            Opcodes.GT,
            Opcodes.SLT,
            Opcodes.SGT,
            Opcodes.EQ,
            Opcodes.ISZERO,
            Opcodes.AND,
            Opcodes.OR,
            Opcodes.XOR,
            Opcodes.NOT,
            Opcodes.BYTE,
            Opcodes.SHA3,
            Opcodes.ADDRESS,
            Opcodes.BALANCE,
            Opcodes.ORIGIN,
            Opcodes.CALLER,
            Opcodes.CALLVALUE,
            Opcodes.CALLDATALOAD,
            Opcodes.CALLDATASIZE,
            Opcodes.CALLDATACOPY,
            Opcodes.CODESIZE,
            Opcodes.CODECOPY,
            Opcodes.GASPRICE,
            Opcodes.EXTCODESIZE,
            Opcodes.EXTCODECOPY,
            Opcodes.BLOCKHASH,
            Opcodes.COINBASE,
            Opcodes.TIMESTAMP,
            Opcodes.NUMBER,
            Opcodes.PREVRANDAO,
            Opcodes.GASLIMIT,
            Opcodes.POP,
            Opcodes.MLOAD,
            Opcodes.MSTORE,
            Opcodes.MSTORE8,
            Opcodes.SLOAD,
            Opcodes.SSTORE,
            Opcodes.PC,
            Opcodes.MSIZE,
            Opcodes.GAS,
            Opcodes.JUMP,
            Opcodes.JUMPI,
            Opcodes.JUMPDEST,
            Opcodes.PUSH1,
            Opcodes.PUSH2,
            Opcodes.PUSH3,
            Opcodes.PUSH4,
            Opcodes.PUSH5,
            Opcodes.PUSH6,
            Opcodes.PUSH7,
            Opcodes.PUSH8,
            Opcodes.PUSH9,
            Opcodes.PUSH10,
            Opcodes.PUSH11,
            Opcodes.PUSH12,
            Opcodes.PUSH13,
            Opcodes.PUSH14,
            Opcodes.PUSH15,
            Opcodes.PUSH16,
            Opcodes.PUSH17,
            Opcodes.PUSH18,
            Opcodes.PUSH19,
            Opcodes.PUSH20,
            Opcodes.PUSH21,
            Opcodes.PUSH22,
            Opcodes.PUSH23,
            Opcodes.PUSH24,
            Opcodes.PUSH25,
            Opcodes.PUSH26,
            Opcodes.PUSH27,
            Opcodes.PUSH28,
            Opcodes.PUSH29,
            Opcodes.PUSH30,
            Opcodes.PUSH31,
            Opcodes.PUSH32,
            Opcodes.DUP1,
            Opcodes.DUP2,
            Opcodes.DUP3,
            Opcodes.DUP4,
            Opcodes.DUP5,
            Opcodes.DUP6,
            Opcodes.DUP7,
            Opcodes.DUP8,
            Opcodes.DUP9,
            Opcodes.DUP10,
            Opcodes.DUP11,
            Opcodes.DUP12,
            Opcodes.DUP13,
            Opcodes.DUP14,
            Opcodes.DUP15,
            Opcodes.DUP16,
            Opcodes.SWAP1,
            Opcodes.SWAP2,
            Opcodes.SWAP3,
            Opcodes.SWAP4,
            Opcodes.SWAP5,
            Opcodes.SWAP6,
            Opcodes.SWAP7,
            Opcodes.SWAP8,
            Opcodes.SWAP9,
            Opcodes.SWAP10,
            Opcodes.SWAP11,
            Opcodes.SWAP12,
            Opcodes.SWAP13,
            Opcodes.SWAP14,
            Opcodes.SWAP15,
            Opcodes.SWAP16,
            Opcodes.LOG0,
            Opcodes.LOG1,
            Opcodes.LOG2,
            Opcodes.LOG3,
            Opcodes.LOG4,
            Opcodes.CREATE,
            Opcodes.CALL,
            Opcodes.CALLCODE,
            Opcodes.RETURN,
            Opcodes.SELFDESTRUCT,
        ]

    @classmethod
    def create_opcodes(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> List[Tuple[Opcodes, EVMCodeType]]:
        """
        At Genesis, only `CREATE` opcode is supported.
        """
        return [
            (Opcodes.CREATE, EVMCodeType.LEGACY),
        ]

    @classmethod
    def pre_allocation(cls) -> Mapping:
        """
        Returns whether the fork expects pre-allocation of accounts

        Frontier does not require pre-allocated accounts
        """
        return {}

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """
        Returns whether the fork expects pre-allocation of accounts

        Frontier does not require pre-allocated accounts
        """
        return {}


class Homestead(Frontier):
    """
    Homestead fork
    """

    @classmethod
    def precompiles(cls, block_number: int = 0, timestamp: int = 0) -> List[Address]:
        """
        At Homestead, EC-recover, SHA256, RIPEMD160, and Identity pre-compiles are introduced
        """
        return list(Address(i) for i in range(1, 5)) + super(Homestead, cls).precompiles(
            block_number, timestamp
        )

    @classmethod
    def call_opcodes(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> List[Tuple[Opcodes, EVMCodeType]]:
        """
        At Homestead, DELEGATECALL opcode was introduced.
        """
        return [(Opcodes.DELEGATECALL, EVMCodeType.LEGACY),] + super(
            Homestead, cls
        ).call_opcodes(block_number, timestamp)

    @classmethod
    def valid_opcodes(
        cls,
    ) -> List[Opcodes]:
        """
        Returns the list of Opcodes that are valid to work on this fork.
        """
        return [Opcodes.DELEGATECALL] + super(Homestead, cls).valid_opcodes()


class Byzantium(Homestead):
    """
    Byzantium fork
    """

    @classmethod
    def get_reward(cls, block_number: int = 0, timestamp: int = 0) -> int:
        """
        At Byzantium, the block reward is reduced to
        3_000_000_000_000_000_000 wei
        """
        return 3_000_000_000_000_000_000

    @classmethod
    def precompiles(cls, block_number: int = 0, timestamp: int = 0) -> List[Address]:
        """
        At Byzantium, pre-compiles for bigint modular exponentiation, addition and scalar
        multiplication on elliptic curve alt_bn128, and optimal ate pairing check on
        elliptic curve alt_bn128 are introduced
        """
        return list(Address(i) for i in range(5, 9)) + super(Byzantium, cls).precompiles(
            block_number, timestamp
        )

    @classmethod
    def call_opcodes(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> List[Tuple[Opcodes, EVMCodeType]]:
        """
        At Byzantium, STATICCALL opcode was introduced.
        """
        return [(Opcodes.STATICCALL, EVMCodeType.LEGACY),] + super(
            Byzantium, cls
        ).call_opcodes(block_number, timestamp)

    @classmethod
    def valid_opcodes(
        cls,
    ) -> List[Opcodes]:
        """
        Returns the list of Opcodes that are valid to work on this fork.
        """
        return [Opcodes.RETURNDATASIZE, Opcodes.STATICCALL] + super(Byzantium, cls).valid_opcodes()


class Constantinople(Byzantium):
    """
    Constantinople fork
    """

    @classmethod
    def get_reward(cls, block_number: int = 0, timestamp: int = 0) -> int:
        """
        At Constantinople, the block reward is reduced to
        2_000_000_000_000_000_000 wei
        """
        return 2_000_000_000_000_000_000

    @classmethod
    def create_opcodes(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> List[Tuple[Opcodes, EVMCodeType]]:
        """
        At Constantinople, `CREATE2` opcode is added.
        """
        return [(Opcodes.CREATE2, EVMCodeType.LEGACY),] + super(
            Constantinople, cls
        ).create_opcodes(block_number, timestamp)

    @classmethod
    def valid_opcodes(
        cls,
    ) -> List[Opcodes]:
        """
        Returns the list of Opcodes that are valid to work on this fork.
        """
        return [
            Opcodes.SHL,
            Opcodes.SHR,
            Opcodes.SAR,
            Opcodes.EXTCODEHASH,
            Opcodes.CREATE2,
        ] + super(Constantinople, cls).valid_opcodes()


class ConstantinopleFix(Constantinople, solc_name="constantinople"):
    """
    Constantinople Fix fork
    """

    pass


class Istanbul(ConstantinopleFix):
    """
    Istanbul fork
    """

    @classmethod
    def precompiles(cls, block_number: int = 0, timestamp: int = 0) -> List[Address]:
        """
        At Istanbul, pre-compile for blake2 compression is introduced
        """
        return [Address(9)] + super(Istanbul, cls).precompiles(block_number, timestamp)

    @classmethod
    def valid_opcodes(
        cls,
    ) -> List[Opcodes]:
        """
        Returns the list of Opcodes that are valid to work on this fork.
        """
        return [Opcodes.CHAINID, Opcodes.SELFBALANCE] + super(Istanbul, cls).valid_opcodes()


# Glacier forks skipped, unless explicitly specified
class MuirGlacier(Istanbul, solc_name="istanbul", ignore=True):
    """
    Muir Glacier fork
    """

    pass


class Berlin(Istanbul):
    """
    Berlin fork
    """

    @classmethod
    def tx_types(cls, block_number: int = 0, timestamp: int = 0) -> List[int]:
        """
        At Berlin, access list transactions are introduced
        """
        return [1] + super(Berlin, cls).tx_types(block_number, timestamp)

    @classmethod
    def contract_creating_tx_types(cls, block_number: int = 0, timestamp: int = 0) -> List[int]:
        """
        At Berlin, access list transactions are introduced
        """
        return [1] + super(Berlin, cls).contract_creating_tx_types(block_number, timestamp)


class London(Berlin):
    """
    London fork
    """

    @classmethod
    def header_base_fee_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Base Fee is required starting from London.
        """
        return True

    @classmethod
    def tx_types(cls, block_number: int = 0, timestamp: int = 0) -> List[int]:
        """
        At London, dynamic fee transactions are introduced
        """
        return [2] + super(London, cls).tx_types(block_number, timestamp)

    @classmethod
    def contract_creating_tx_types(cls, block_number: int = 0, timestamp: int = 0) -> List[int]:
        """
        At London, dynamic fee transactions are introduced
        """
        return [2] + super(London, cls).contract_creating_tx_types(block_number, timestamp)

    @classmethod
    def valid_opcodes(
        cls,
    ) -> List[Opcodes]:
        """
        Returns the list of Opcodes that are valid to work on this fork.
        """
        return [Opcodes.BASEFEE] + super(London, cls).valid_opcodes()


# Glacier forks skipped, unless explicitly specified
class ArrowGlacier(London, solc_name="london", ignore=True):
    """
    Arrow Glacier fork
    """

    pass


class GrayGlacier(ArrowGlacier, solc_name="london", ignore=True):
    """
    Gray Glacier fork
    """

    pass


class Paris(
    London,
    transition_tool_name="Merge",
    blockchain_test_network_name="Paris",
):
    """
    Paris (Merge) fork
    """

    @classmethod
    def header_prev_randao_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Prev Randao is required starting from Paris.
        """
        return True

    @classmethod
    def header_zero_difficulty_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Zero difficulty is required starting from Paris.
        """
        return True

    @classmethod
    def get_reward(cls, block_number: int = 0, timestamp: int = 0) -> int:
        """
        Paris updates the reward to 0.
        """
        return 0

    @classmethod
    def engine_new_payload_version(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """
        Starting at Paris, payloads can be sent through the engine API
        """
        return 1


class Shanghai(Paris):
    """
    Shanghai fork
    """

    @classmethod
    def header_withdrawals_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Withdrawals are required starting from Shanghai.
        """
        return True

    @classmethod
    def engine_new_payload_version(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """
        Starting at Shanghai, new payload calls must use version 2
        """
        return 2

    @classmethod
    def valid_opcodes(
        cls,
    ) -> List[Opcodes]:
        """
        Returns the list of Opcodes that are valid to work on this fork.
        """
        return [Opcodes.PUSH0] + super(Shanghai, cls).valid_opcodes()


class Cancun(Shanghai):
    """
    Cancun fork
    """

    @classmethod
    def solc_min_version(cls) -> Version:
        """
        Returns the minimum version of solc that supports this fork.
        """
        return Version.parse("0.8.24")

    @classmethod
    def header_excess_blob_gas_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Excess blob gas is required starting from Cancun.
        """
        return True

    @classmethod
    def header_blob_gas_used_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Blob gas used is required starting from Cancun.
        """
        return True

    @classmethod
    def header_beacon_root_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Parent beacon block root is required starting from Cancun.
        """
        return True

    @classmethod
    def blob_gas_per_blob(cls, block_number: int, timestamp: int) -> int:
        """
        Blobs are enabled started from Cancun.
        """
        return 2**17

    @classmethod
    def tx_types(cls, block_number: int = 0, timestamp: int = 0) -> List[int]:
        """
        At Cancun, blob type transactions are introduced
        """
        return [3] + super(Cancun, cls).tx_types(block_number, timestamp)

    @classmethod
    def precompiles(cls, block_number: int = 0, timestamp: int = 0) -> List[Address]:
        """
        At Cancun, pre-compile for kzg point evaluation is introduced
        """
        return [Address(0xA)] + super(Cancun, cls).precompiles(block_number, timestamp)

    @classmethod
    def system_contracts(cls, block_number: int = 0, timestamp: int = 0) -> List[Address]:
        """
        Cancun introduces the system contract for EIP-4788
        """
        return [Address(0x000F3DF6D732807EF1319FB7B8BB8522D0BEAC02)]

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """
        Cancun requires pre-allocation of the beacon root contract for EIP-4788 on blockchain
        type tests
        """
        new_allocation = {
            0x000F3DF6D732807EF1319FB7B8BB8522D0BEAC02: {
                "nonce": 1,
                "code": "0x3373fffffffffffffffffffffffffffffffffffffffe14604d57602036146024575f5f"
                "fd5b5f35801560495762001fff810690815414603c575f5ffd5b62001fff01545f5260205ff35b5f"
                "5ffd5b62001fff42064281555f359062001fff015500",
            }
        }
        return new_allocation | super(Cancun, cls).pre_allocation_blockchain()

    @classmethod
    def engine_new_payload_version(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """
        Starting at Cancun, new payload calls must use version 3
        """
        return 3

    @classmethod
    def engine_new_payload_blob_hashes(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Starting at Cancun, payloads must have blob hashes.
        """
        return True

    @classmethod
    def engine_new_payload_beacon_root(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Starting at Cancun, payloads must have a parent beacon block root.
        """
        return True

    @classmethod
    def valid_opcodes(
        cls,
    ) -> List[Opcodes]:
        """
        Returns the list of Opcodes that are valid to work on this fork.
        """
        return [
            Opcodes.BLOBHASH,
            Opcodes.BLOBBASEFEE,
            Opcodes.TLOAD,
            Opcodes.TSTORE,
            Opcodes.MCOPY,
        ] + super(Cancun, cls).valid_opcodes()


class Prague(Cancun):
    """
    Prague fork
    """

    @classmethod
    def is_deployed(cls) -> bool:
        """
        Flags that the fork has not been deployed to mainnet; it is under active
        development.
        """
        return False

    @classmethod
    def solc_min_version(cls) -> Version:
        """
        Returns the minimum version of solc that supports this fork.
        """
        return Version.parse("1.0.0")  # set a high version; currently unknown

    @classmethod
    def precompiles(cls, block_number: int = 0, timestamp: int = 0) -> List[Address]:
        """
        At Prague, pre-compile for BLS operations are added:

        G1ADD = 0x0B
        G1MUL = 0x0C
        G1MSM = 0x0D
        G2ADD = 0x0E
        G2MUL = 0x0F
        G2MSM = 0x10
        PAIRING = 0x11
        MAP_FP_TO_G1 = 0x12
        MAP_FP2_TO_G2 = 0x13
        """
        return list(Address(i) for i in range(0xB, 0x13 + 1)) + super(Prague, cls).precompiles(
            block_number, timestamp
        )

    @classmethod
    def system_contracts(cls, block_number: int = 0, timestamp: int = 0) -> List[Address]:
        """
        Prague introduces the system contracts for EIP-6110, EIP-7002, EIP-7251 and EIP-2935
        """
        return [
            Address(0x00000000219AB540356CBB839CBE05303D7705FA),
            Address(0x00A3CA265EBCB825B45F985A16CEFB49958CE017),
            Address(0x00B42DBF2194E931E80326D950320F7D9DBEAC02),
            Address(0x0AAE40965E6800CD9B1F4B05FF21581047E3F91E),
        ] + super(Prague, cls).system_contracts(block_number, timestamp)

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """
        Prague requires pre-allocation of the beacon chain deposit contract for EIP-6110,
        the exits contract for EIP-7002, and the history storage contract for EIP-2935.
        """
        new_allocation = {}

        # Add the beacon chain deposit contract
        DEPOSIT_CONTRACT_TREE_DEPTH = 32
        storage = {}
        next_hash = sha256(b"\x00" * 64).digest()
        for i in range(DEPOSIT_CONTRACT_TREE_DEPTH + 2, DEPOSIT_CONTRACT_TREE_DEPTH * 2 + 1):
            storage[i] = next_hash
            next_hash = sha256(next_hash + next_hash).digest()

        with open(CURRENT_FOLDER / "contracts" / "deposit_contract.bin", mode="rb") as f:
            new_allocation.update(
                {
                    0x00000000219AB540356CBB839CBE05303D7705FA: {
                        "nonce": 1,
                        "code": f.read(),
                        "storage": storage,
                    }
                }
            )

        # Add the withdrawal request contract
        with open(CURRENT_FOLDER / "contracts" / "withdrawal_request.bin", mode="rb") as f:
            new_allocation.update(
                {
                    0x00A3CA265EBCB825B45F985A16CEFB49958CE017: {
                        "nonce": 1,
                        "code": f.read(),
                    },
                }
            )

        # Add the consolidation request contract
        with open(CURRENT_FOLDER / "contracts" / "consolidation_request.bin", mode="rb") as f:
            new_allocation.update(
                {
                    0x00B42DBF2194E931E80326D950320F7D9DBEAC02: {
                        "nonce": 1,
                        "code": f.read(),
                    },
                }
            )

        # Add the history storage contract
        with open(CURRENT_FOLDER / "contracts" / "history_contract.bin", mode="rb") as f:
            new_allocation.update(
                {
                    0x0AAE40965E6800CD9B1F4B05FF21581047E3F91E: {
                        "nonce": 1,
                        "code": f.read(),
                    }
                }
            )

        return new_allocation | super(Prague, cls).pre_allocation_blockchain()

    @classmethod
    def header_requests_required(cls, block_number: int, timestamp: int) -> bool:
        """
        Prague requires that the execution layer block contains the beacon
        chain requests.
        """
        return True

    @classmethod
    def engine_new_payload_version(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """
        Starting at Prague, new payload calls must use version 4
        """
        return 4

    @classmethod
    def engine_forkchoice_updated_version(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """
        At Prague, version number of NewPayload and ForkchoiceUpdated diverge.
        """
        return 3


class CancunEIP7692(  # noqa: SC200
    Cancun,
    transition_tool_name="Prague",  # Evmone enables (only) EOF at Prague
    blockchain_test_network_name="Prague",  # Evmone enables (only) EOF at Prague
    solc_name="cancun",
):
    """
    Cancun + EIP-7692 (EOF) fork
    """

    @classmethod
    def evm_code_types(cls, block_number: int = 0, timestamp: int = 0) -> List[EVMCodeType]:
        """
        EOF V1 is supported starting from this fork.
        """
        return super(CancunEIP7692, cls,).evm_code_types(  # noqa: SC200
            block_number,
            timestamp,
        ) + [EVMCodeType.EOF_V1]

    @classmethod
    def call_opcodes(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> List[Tuple[Opcodes, EVMCodeType]]:
        """
        EOF V1 introduces EXTCALL, EXTSTATICCALL, EXTDELEGATECALL.
        """
        return [
            (Opcodes.EXTCALL, EVMCodeType.EOF_V1),
            (Opcodes.EXTSTATICCALL, EVMCodeType.EOF_V1),
            (Opcodes.EXTDELEGATECALL, EVMCodeType.EOF_V1),
        ] + super(
            CancunEIP7692, cls  # noqa: SC200
        ).call_opcodes(
            block_number, timestamp
        )

    @classmethod
    def create_opcodes(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> List[Tuple[Opcodes, EVMCodeType]]:
        """
        EOF V1 introduces `EOFCREATE`.
        """
        return [(Opcodes.EOFCREATE, EVMCodeType.EOF_V1),] + super(
            CancunEIP7692, cls  # noqa: SC200
        ).create_opcodes(block_number, timestamp)

    @classmethod
    def is_deployed(cls) -> bool:
        """
        Flags that the fork has not been deployed to mainnet; it is under active
        development.
        """
        return False

    @classmethod
    def solc_min_version(cls) -> Version:
        """
        Returns the minimum version of solc that supports this fork.
        """
        return Version.parse("1.0.0")  # set a high version; currently unknown


class PragueEIP7692(  # noqa: SC200
    Prague,
    transition_tool_name="Prague",  # Besu enables EOF at Prague
    blockchain_test_network_name="Prague",  # Besu enables EOF at Prague
    solc_name="cancun",
):
    """
    Prague + EIP-7692 (EOF) fork
    """

    @classmethod
    def evm_code_types(cls, block_number: int = 0, timestamp: int = 0) -> List[EVMCodeType]:
        """
        EOF V1 is supported starting from this fork.
        """
        return super(PragueEIP7692, cls,).evm_code_types(  # noqa: SC200
            block_number,
            timestamp,
        ) + [EVMCodeType.EOF_V1]

    @classmethod
    def call_opcodes(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> List[Tuple[Opcodes, EVMCodeType]]:
        """
        EOF V1 introduces EXTCALL, EXTSTATICCALL, EXTDELEGATECALL.
        """
        return [
            (Opcodes.EXTCALL, EVMCodeType.EOF_V1),
            (Opcodes.EXTSTATICCALL, EVMCodeType.EOF_V1),
            (Opcodes.EXTDELEGATECALL, EVMCodeType.EOF_V1),
        ] + super(
            PragueEIP7692, cls  # noqa: SC200
        ).call_opcodes(
            block_number, timestamp
        )

    @classmethod
    def is_deployed(cls) -> bool:
        """
        Flags that the fork has not been deployed to mainnet; it is under active
        development.
        """
        return False

    @classmethod
    def solc_min_version(cls) -> Version:
        """
        Returns the minimum version of solc that supports this fork.
        """
        return Version.parse("1.0.0")  # set a high version; currently unknown
