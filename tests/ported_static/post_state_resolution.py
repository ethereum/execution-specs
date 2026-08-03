"""
Runtime post-state resolution for ported static tests.

Provides resolve_expect_post / resolve_expect_post_fork, used by the tests
under tests/ported_static/ to resolve expected post-state and exceptions for
a given (d, g, v) and fork. Relocated out of the deleted specs/static_state/
parser.
"""

import re
from enum import StrEnum
from typing import Any, Iterator, Set

from execution_testing.base_types import EthereumTestRootModel
from execution_testing.exceptions import TransactionExceptionInstanceOrList
from execution_testing.forks import Fork, get_forks
from pydantic import BaseModel, field_validator, model_validator


class CMP(StrEnum):
    """Comparison action."""

    LE = "<="
    GE = ">="
    LT = "<"
    GT = ">"
    EQ = "="


class ForkConstraint(BaseModel):
    """Single fork with an operand."""

    operand: CMP
    fork: Fork

    @field_validator("fork", mode="before")
    @classmethod
    def parse_fork_synonyms(cls, value: Any) -> Any:
        """Resolve fork synonyms."""
        if value == "EIP158":
            value = "Byzantium"
        return value

    @model_validator(mode="before")
    @classmethod
    def parse_from_string(cls, data: Any) -> Any:
        """Parse a fork with operand from a string."""
        if isinstance(data, str):
            for cmp in CMP:
                if data.startswith(cmp):
                    fork = data.removeprefix(cmp)
                    return {
                        "operand": cmp,
                        "fork": fork,
                    }
            return {
                "operand": CMP.EQ,
                "fork": data,
            }
        return data

    def match(self, fork: Fork) -> bool:
        """Return whether the fork satisfies the operand evaluation."""
        match self.operand:
            case CMP.LE:
                return fork <= self.fork
            case CMP.GE:
                return fork >= self.fork
            case CMP.LT:
                return fork < self.fork
            case CMP.GT:
                return fork > self.fork
            case CMP.EQ:
                return fork == self.fork
            case _:
                raise ValueError(f"Invalid operand: {self.operand}")


class ForkSet(EthereumTestRootModel):
    """Set of forks."""

    root: Set[Fork]

    @model_validator(mode="before")
    @classmethod
    def parse_from_list_or_string(cls, value: Any) -> Set[Fork]:
        """Parse fork_with_operand `>=Cancun` into {Cancun, Prague, ...}."""
        fork_set: Set[Fork] = set()
        if not isinstance(value, list):
            value = [value]

        for fork_with_operand in value:
            matches = re.findall(r"(<=|<|>=|>|=)([^<>=]+)", fork_with_operand)
            if matches:
                all_fork_constraints = [
                    ForkConstraint.model_validate(f"{op}{fork.strip()}")
                    for op, fork in matches
                ]
            else:
                all_fork_constraints = [
                    ForkConstraint.model_validate(fork_with_operand.strip())
                ]

            for fork in get_forks():
                for f in all_fork_constraints:
                    if not f.match(fork):
                        # If any constraint does not match, skip adding
                        break
                else:
                    # All constraints match, add the fork to the set
                    fork_set.add(fork)

        return fork_set

    def __hash__(self) -> int:
        """Return the hash of the fork set."""
        h = hash(None)
        for fork in sorted([str(f) for f in self]):
            h ^= hash(fork)
        return h

    def __contains__(self, fork: Fork) -> bool:
        """Check if the fork set contains a fork."""
        return fork in self.root

    def __iter__(self) -> Iterator[Fork]:  # type: ignore[override]
        """Iterate over the fork set."""
        return iter(self.root)

    def __len__(self) -> int:
        """Return the length of the fork set."""
        return len(self.root)


def _match_index(idx: int | list, val: int) -> bool:
    """Check if an index specification matches a value."""
    if isinstance(idx, int):
        return idx == -1 or idx == val
    if isinstance(idx, list):
        return val in idx
    return False


def resolve_expect_post(
    expect_entries: list[dict],
    d: int,
    g: int,
    v: int,
    fork: Fork,
) -> tuple[dict, TransactionExceptionInstanceOrList | None]:
    """
    Resolve expected post-state for given d, g, v and fork.

    Used by generated Python tests at runtime. The expect_entries are
    materialized Python dicts with resolved addresses and Account objects.
    """
    for entry in expect_entries:
        indexes = entry["indexes"]
        if not _match_index(indexes.get("data", -1), d):
            continue
        if not _match_index(indexes.get("gas", -1), g):
            continue
        if not _match_index(indexes.get("value", -1), v):
            continue

        # Match fork against network constraints
        network = entry["network"]
        fork_set = ForkSet.model_validate(network)
        if fork not in fork_set:
            continue

        # Found matching entry
        result = entry.get("result", {})

        # Resolve exception
        exception: TransactionExceptionInstanceOrList | None = None
        expect_exc = entry.get("expect_exception")
        if expect_exc:
            for constraint_str, exc_value in expect_exc.items():
                exc_fork_set = ForkSet.model_validate(
                    constraint_str.split(",")
                )
                if fork in exc_fork_set:
                    exception = exc_value
                    break

        return result, exception

    raise ValueError(
        f"No matching expect entry for d={d}, g={g}, v={v}, fork={fork}"
    )


def resolve_expect_post_fork(
    expect_entries: list[dict],
    fork: Fork,
) -> tuple[dict, TransactionExceptionInstanceOrList | None]:
    """
    Resolve expected post-state for a given fork only (no d/g/v matching).

    Used by single-case generated Python tests that have fork-dependent
    post-state (multiple expect sections with different networks but only
    one (d, g, v) combo).
    """
    for entry in expect_entries:
        # Match fork against network constraints
        network = entry["network"]
        fork_set = ForkSet.model_validate(network)
        if fork not in fork_set:
            continue

        # Found matching entry
        result = entry.get("result", {})

        # Resolve exception
        exception: TransactionExceptionInstanceOrList | None = None
        expect_exc = entry.get("expect_exception")
        if expect_exc:
            for constraint_str, exc_value in expect_exc.items():
                exc_fork_set = ForkSet.model_validate(
                    constraint_str.split(",")
                )
                if fork in exc_fork_set:
                    exception = exc_value
                    break

        return result, exception

    raise ValueError(f"No matching expect entry for fork={fork}")
