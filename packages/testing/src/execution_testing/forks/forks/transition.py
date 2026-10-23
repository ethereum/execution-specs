"""List of all transition fork definitions."""

from types import new_class
from typing import Type

from ..base_fork import BaseFork
from ..transition_base_fork import TransitionBaseClass, transition_fork
from .forks import (
    BPO1,
    BPO2,
    BPO3,
    BPO4,
    BPO_SCENARIOS,
    Amsterdam,
    Berlin,
    Bogota,
    Cancun,
    London,
    Osaka,
    Paris,
    Prague,
    Shanghai,
)


# Transition Forks
@transition_fork(to_fork=London, from_fork=Berlin, at_block=5)
class BerlinToLondonAt5(TransitionBaseClass):
    """Berlin to London transition at Block 5."""

    pass


@transition_fork(to_fork=Shanghai, from_fork=Paris, at_timestamp=15_000)
class ParisToShanghaiAtTime15k(TransitionBaseClass):
    """Paris to Shanghai transition at Timestamp 15k."""

    pass


@transition_fork(to_fork=Cancun, from_fork=Shanghai, at_timestamp=15_000)
class ShanghaiToCancunAtTime15k(TransitionBaseClass):
    """Shanghai to Cancun transition at Timestamp 15k."""

    pass


@transition_fork(to_fork=Prague, from_fork=Cancun, at_timestamp=15_000)
class CancunToPragueAtTime15k(TransitionBaseClass):
    """Cancun to Prague transition at Timestamp 15k."""

    pass


@transition_fork(to_fork=Osaka, from_fork=Prague, at_timestamp=15_000)
class PragueToOsakaAtTime15k(TransitionBaseClass):
    """Prague to Osaka transition at Timestamp 15k."""

    pass


@transition_fork(to_fork=BPO1, from_fork=Osaka, at_timestamp=15_000)
class OsakaToBPO1AtTime15k(TransitionBaseClass):
    """Osaka to BPO1 transition at Timestamp 15k."""

    pass


@transition_fork(to_fork=BPO2, from_fork=BPO1, at_timestamp=15_000)
class BPO1ToBPO2AtTime15k(TransitionBaseClass):
    """BPO1 to BPO2 transition at Timestamp 15k."""

    pass


@transition_fork(to_fork=Amsterdam, from_fork=BPO2, at_timestamp=15_000)
class BPO2ToAmsterdamAtTime15k(TransitionBaseClass):
    """BPO2 to Amsterdam transition at Timestamp 15k."""

    # TODO: We may need to adjust which BPO Amsterdam inherits from as the
    #  related Amsterdam specs change over time, and before Amsterdam is
    #  live on mainnet.

    pass


@transition_fork(to_fork=Bogota, from_fork=Amsterdam, at_timestamp=15_000)
class AmsterdamToBogotaAtTime15k(TransitionBaseClass):
    """Amsterdam to Bogota transition at Timestamp 15k."""

    pass


@transition_fork(to_fork=BPO3, from_fork=BPO2, at_timestamp=15_000)
class BPO2ToBPO3AtTime15k(TransitionBaseClass):
    """BPO2 to BPO3 transition at Timestamp 15k."""

    pass


@transition_fork(to_fork=BPO4, from_fork=BPO3, at_timestamp=15_000)
class BPO3ToBPO4AtTime15k(TransitionBaseClass):
    """BPO3 to BPO4 transition at Timestamp 15k."""

    pass


def add_bpo_scenario_transition(
    from_fork: Type[BaseFork], to_fork: Type[BaseFork]
) -> None:
    """
    Add the transition from `from_fork` to `to_fork` at timestamp 15k.

    The name leaves out the fork prefix of a scenario of `from_fork`, as in
    `AmsterdamToBPOIncreaseAtTime15k`.
    """
    to_name = to_fork.name().removeprefix(from_fork.name())
    name = f"{from_fork.name()}To{to_name}AtTime15k"
    doc = f"{from_fork.name()} to {to_name} transition at Timestamp 15k."
    globals()[name] = transition_fork(
        to_fork=to_fork, from_fork=from_fork, at_timestamp=15_000
    )(
        new_class(
            name,
            (TransitionBaseClass,),
            exec_body=lambda namespace: namespace.update(
                __module__=__name__, __doc__=doc
            ),
        )
    )


def add_bpo_scenario_transitions() -> None:
    """Add the transitions from each fork into its BPO scenarios at 15k."""
    for fork, scenarios in BPO_SCENARIOS.items():
        for scenario in scenarios:
            add_bpo_scenario_transition(fork, scenario)


add_bpo_scenario_transitions()
