"""
All Ethereum fork class definitions.
"""

from typing import List, Mapping, Optional

from semver import Version

from ..base_fork import BaseFork


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
    def precompiles(cls, block_number: int = 0, timestamp: int = 0) -> List[int]:
        """
        At Genesis, no pre-compiles are allowed
        """
        return []

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
    def precompiles(cls, block_number: int = 0, timestamp: int = 0) -> List[int]:
        """
        At Homestead, EC-recover, SHA256, RIPEMD160, and Identity pre-compiles are introduced
        """
        return [1, 2, 3, 4] + super(Homestead, cls).precompiles(block_number, timestamp)


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
    def precompiles(cls, block_number: int = 0, timestamp: int = 0) -> List[int]:
        """
        At Byzantium, pre-compiles for bigint modular exponentiation, addition and scalar
        multiplication on elliptic curve alt_bn128, and optimal ate pairing check on
        elliptic curve alt_bn128 are introduced
        """
        return [5, 6, 7, 8] + super(Byzantium, cls).precompiles(block_number, timestamp)


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
    def precompiles(cls, block_number: int = 0, timestamp: int = 0) -> List[int]:
        """
        At Istanbul, pre-compile for blake2 compression is introduced
        """
        return [9] + super(Istanbul, cls).precompiles(block_number, timestamp)


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
    blockchain_test_network_name="Merge",
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


class Cancun(Shanghai):
    """
    Cancun fork
    """

    @classmethod
    def is_deployed(cls):
        """
        Flags that Cancun has not been deployed to mainnet; it is under active
        development.
        """
        return False

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
    def precompiles(cls, block_number: int = 0, timestamp: int = 0) -> List[int]:
        """
        At Cancun, pre-compile for kzg point evaluation is introduced
        """
        return [0xA] + super(Cancun, cls).precompiles(block_number, timestamp)

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
