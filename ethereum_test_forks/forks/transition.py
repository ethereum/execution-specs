"""
List of all transition fork definitions.
"""
from ..transition_base_fork import transition_fork
from .forks import Berlin, Cancun, London, Paris, Shanghai


# Transition Forks
@transition_fork(to_fork=London, at_block=5)
class BerlinToLondonAt5(Berlin):
    """
    Berlin to London transition at Block 5
    """

    pass


@transition_fork(to_fork=Shanghai, at_timestamp=15_000)
class ParisToShanghaiAtTime15k(Paris, blockchain_test_network_name="ParisToShanghaiAtTime15k"):
    """
    Paris to Shanghai transition at Timestamp 15k
    """

    pass


@transition_fork(to_fork=Cancun, at_timestamp=15_000)
class ShanghaiToCancunAtTime15k(Shanghai):
    """
    Shanghai to Cancun transition at Timestamp 15k
    """

    pass
