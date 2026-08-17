"""
Fork registry and schedule resolution for the engine server.

Each post-merge fork maps to its Engine API wire family: the
`engine_newPayloadVX` / `engine_forkchoiceUpdatedVX` versions it
answers to and the payload fields it carries. Fork modules are
resolved dynamically from `ethereum.forks.<package>`.
"""

import importlib
from dataclasses import dataclass
from functools import cache
from types import ModuleType
from typing import List, Mapping, Optional, Tuple


@dataclass(frozen=True)
class ForkSpec:
    """Wire-level description of one post-merge fork."""

    name: str
    """Fork name as used in fixtures and `HIVE_<NAME>_TIMESTAMP`."""

    package: str
    """Package name under `ethereum.forks`."""

    has_withdrawals: bool
    has_blobs: bool
    has_requests: bool
    has_bal: bool

    @property
    def fork(self) -> ModuleType:
        """The fork's `fork` module."""
        return _module(self.package, "fork")

    @property
    def engine(self) -> ModuleType:
        """The fork's `execution_engine` module."""
        return _module(self.package, "execution_engine")

    @property
    def blocks(self) -> ModuleType:
        """The fork's `blocks` module."""
        return _module(self.package, "blocks")

    @property
    def transactions(self) -> ModuleType:
        """The fork's `transactions` module."""
        return _module(self.package, "transactions")


@cache
def _module(package: str, name: str) -> ModuleType:
    return importlib.import_module(f"ethereum.forks.{package}.{name}")


FORKS: List[ForkSpec] = [
    ForkSpec("Paris", "paris", False, False, False, False),
    ForkSpec("Shanghai", "shanghai", True, False, False, False),
    ForkSpec("Cancun", "cancun", True, True, False, False),
    ForkSpec("Prague", "prague", True, True, True, False),
    ForkSpec("Osaka", "osaka", True, True, True, False),
    ForkSpec("BPO1", "bpo1", True, True, True, False),
    ForkSpec("BPO2", "bpo2", True, True, True, False),
    ForkSpec("BPO3", "bpo3", True, True, True, False),
    ForkSpec("BPO4", "bpo4", True, True, True, False),
    ForkSpec("BPO5", "bpo5", True, True, True, False),
    ForkSpec("Amsterdam", "amsterdam", True, True, True, True),
    # Pseudo-fork: labels the sidecar wire family while the spec has no
    # dedicated Bogota fork module; execution uses the amsterdam module.
    ForkSpec("Bogota", "amsterdam", True, True, True, True),
]
"""All supported forks, oldest first."""

Schedule = List[Tuple[ForkSpec, int]]
"""Activation timestamps per fork, oldest first."""


def schedule_from_env(env: Mapping[str, str]) -> Schedule:
    """
    Build the fork schedule from hive `HIVE_<NAME>_TIMESTAMP` variables.

    Paris is always active from genesis. A fork without a timestamp
    variable never activates.
    """
    schedule: Schedule = [(FORKS[0], 0)]
    for spec in FORKS[1:]:
        value: Optional[str] = env.get(f"HIVE_{spec.name.upper()}_TIMESTAMP")
        if value is not None:
            schedule.append((spec, int(value)))
    schedule.sort(key=lambda entry: entry[1])
    return schedule


def fork_at(schedule: Schedule, timestamp: int) -> ForkSpec:
    """Return the active fork at `timestamp`."""
    active = schedule[0][0]
    for spec, activation in schedule:
        if timestamp >= activation:
            active = spec
    return active
