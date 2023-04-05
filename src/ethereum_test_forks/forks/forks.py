"""
All Ethereum fork class definitions.
"""
from ..base_fork import BaseFork


# All forks must be listed here !!! in the order they were introduced !!!
class Frontier(BaseFork):
    """
    Frontier fork
    """

    pass


class Homestead(Frontier):
    """
    Homestead fork
    """

    pass


class Byzantium(Homestead):
    """
    Byzantium fork
    """

    pass


class Constantinople(Byzantium):
    """
    Constantinople fork
    """

    pass


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
    def header_base_fee_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
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
    def header_prev_randao_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Prev Randao is required starting from Merge.
        """
        return True

    @classmethod
    def header_zero_difficulty_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Zero difficulty is required starting from Merge.
        """
        return True

    @classmethod
    def get_reward(cls, block_number: int, timestamp: int) -> int:
        """
        Merge updates the reward to 0.
        """
        return 0


class Shanghai(Merge):
    """
    Shanghai fork
    """

    @classmethod
    def header_withdrawals_required(
        cls, block_number: int, timestamp: int
    ) -> bool:
        """
        Withdrawals are required starting from Shanghai.
        """
        return True
