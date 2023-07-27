"""
All Ethereum fork class definitions.
"""
from typing import Optional

from ..base_fork import BaseFork


# All forks must be listed here !!! in the order they were introduced !!!
class Frontier(BaseFork):
    """
    Frontier fork
    """

    @classmethod
    def fork(cls, block_number: int = 0, timestamp: int = 0) -> str:
        """
        Returns fork name as it's meant to be passed to the transition tool for execution.
        """
        return cls.name()

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
    def get_reward(cls, block_number: int = 0, timestamp: int = 0) -> int:
        """
        At Genesis the expected reward amount in wei is
        5_000_000_000_000_000_000
        """
        return 5_000_000_000_000_000_000


class Homestead(Frontier):
    """
    Homestead fork
    """

    pass


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


class ConstantinopleFix(Constantinople):
    """
    Constantinople Fix fork
    """

    pass


class Istanbul(ConstantinopleFix):
    """
    Istanbul fork
    """

    pass


# Glacier forks skipped, unless explicitly specified
class MuirGlacier(Istanbul):
    """
    Muir Glacier fork
    """

    pass


class Berlin(Istanbul):
    """
    Berlin fork
    """

    pass


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


# Glacier forks skipped, unless explicitly specified
class ArrowGlacier(London):
    """
    Arrow Glacier fork
    """

    pass


class GrayGlacier(ArrowGlacier):
    """
    Gray Glacier fork
    """

    pass


class Merge(London):
    """
    Merge fork
    """

    @classmethod
    def header_prev_randao_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Prev Randao is required starting from Merge.
        """
        return True

    @classmethod
    def header_zero_difficulty_required(cls, block_number: int = 0, timestamp: int = 0) -> bool:
        """
        Zero difficulty is required starting from Merge.
        """
        return True

    @classmethod
    def get_reward(cls, block_number: int = 0, timestamp: int = 0) -> int:
        """
        Merge updates the reward to 0.
        """
        return 0

    @classmethod
    def engine_new_payload_version(
        cls, block_number: int = 0, timestamp: int = 0
    ) -> Optional[int]:
        """
        Starting at the merge, payloads can be sent through the engine API
        """
        return 1


class Shanghai(Merge):
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
