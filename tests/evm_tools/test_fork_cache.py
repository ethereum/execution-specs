"""Tests for temporary fork caching."""

import importlib
from typing import Any

import pytest
from ethereum_types.numeric import U64, Uint
from typing_extensions import assert_never

from ethereum.fork_criteria import (
    ByBlockNumber,
    ByTimestamp,
    Unscheduled,
)
from ethereum_spec_tools.evm_tools.t8n import ForkCache
from ethereum_spec_tools.forks import Hardfork

pytestmark = pytest.mark.evm_tools

OVERRIDE_FIELDS: tuple[str, ...] = (
    "blob_target_gas_per_block",
    "gas_per_blob",
    "blob_min_gasprice",
    "blob_base_fee_update_fraction",
    "max_blob_gas_per_block",
    "blob_schedule_target",
    "blob_schedule_max",
)


class DummyTemporaryFork:
    """Stand-in for a cloned hardfork."""

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        """Support ForkCache cleanup."""


def _template() -> Hardfork:
    """Return the Amsterdam fork template."""
    return Hardfork(importlib.import_module("ethereum.forks.amsterdam"))


def _different_fork_criteria(
    criteria: ByBlockNumber | ByTimestamp | Unscheduled,
) -> ByBlockNumber | ByTimestamp | Unscheduled:
    """Return a fork criterion that differs from `criteria`."""
    if isinstance(criteria, ByBlockNumber):
        return ByBlockNumber(int(criteria.block_number) + 1)

    if isinstance(criteria, ByTimestamp):
        return ByTimestamp(int(criteria.timestamp) + 1)

    if isinstance(criteria, Unscheduled):
        zero_order = Unscheduled(order_index=0)
        if criteria == zero_order:
            return Unscheduled(order_index=1)
        return zero_order

    assert_never(criteria)


def _gas_default(
    gas_mod: Any,
    gas_costs_attr: str,
) -> U64 | Uint | None:
    """Return a gas default from `GasCosts`."""
    gas_costs = getattr(gas_mod, "GasCosts", None)
    if gas_costs is None:
        return None

    value = getattr(gas_costs, gas_costs_attr, None)
    if value is None:
        return None

    assert isinstance(value, U64 | Uint)
    return value


def _override_defaults(template: Hardfork) -> dict[str, U64 | Uint]:
    """Return template defaults keyed by ForkCache override name."""
    gas_mod = template.module("vm.gas")
    fork_mod = template.module("fork")

    defaults: dict[str, U64 | Uint | None] = {
        "blob_target_gas_per_block": _gas_default(
            gas_mod,
            "BLOB_TARGET_GAS_PER_BLOCK",
        ),
        "gas_per_blob": _gas_default(gas_mod, "PER_BLOB"),
        "blob_min_gasprice": _gas_default(gas_mod, "BLOB_MIN_GASPRICE"),
        "blob_base_fee_update_fraction": _gas_default(
            gas_mod,
            "BLOB_BASE_FEE_UPDATE_FRACTION",
        ),
        "max_blob_gas_per_block": getattr(
            fork_mod,
            "MAX_BLOB_GAS_PER_BLOCK",
            None,
        ),
        "blob_schedule_target": _gas_default(gas_mod, "BLOB_SCHEDULE_TARGET"),
        "blob_schedule_max": _gas_default(gas_mod, "BLOB_SCHEDULE_MAX"),
    }

    missing = sorted(
        name for name in OVERRIDE_FIELDS if defaults.get(name) is None
    )
    if missing:
        raise AssertionError(
            "missing template defaults for overrides: " + ", ".join(missing)
        )

    return {key: value for key, value in defaults.items() if value is not None}


def test_fork_cache_returns_template_without_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return the template when no overrides are provided."""
    template = _template()

    def clone(*args: Any, **kwargs: Any) -> DummyTemporaryFork:
        pytest.fail("Hardfork.clone() should not run without overrides")

    monkeypatch.setattr(Hardfork, "clone", clone)

    with ForkCache() as cache:
        fork = cache.get(template)

    assert fork is template


def test_fork_cache_returns_template_for_identical_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return the template when requested overrides match it exactly."""
    template = _template()
    identical_overrides = _override_defaults(template)
    identical_fork_criteria = template.criteria
    assert isinstance(
        identical_fork_criteria,
        ByBlockNumber | ByTimestamp | Unscheduled,
    )

    def clone(*args: Any, **kwargs: Any) -> DummyTemporaryFork:
        pytest.fail("Hardfork.clone() should not run for identical overrides")

    monkeypatch.setattr(Hardfork, "clone", clone)

    with ForkCache() as cache:
        fork = cache.get(
            template,
            fork_criteria=identical_fork_criteria,
            **identical_overrides,
        )

    assert fork is template


def test_fork_cache_clones_when_fork_criteria_changes_template(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clone the template when the fork criteria changes."""
    template = _template()
    cloned = DummyTemporaryFork()
    seen: dict[str, Any] = {}

    def clone(*args: Any, **kwargs: Any) -> DummyTemporaryFork:
        seen.update(kwargs)
        return cloned

    monkeypatch.setattr(Hardfork, "clone", clone)

    template_criteria = template.criteria
    assert isinstance(
        template_criteria,
        ByBlockNumber | ByTimestamp | Unscheduled,
    )
    changed_fork_criteria = _different_fork_criteria(template_criteria)

    with ForkCache() as cache:
        fork = cache.get(template, fork_criteria=changed_fork_criteria)

    assert fork is cloned
    assert seen["template"] is template
    assert seen["fork_criteria"] == changed_fork_criteria


@pytest.mark.parametrize("field", OVERRIDE_FIELDS)
def test_fork_cache_returns_template_for_each_identical_blob_override(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    """Return the template when each blob-related override matches it."""
    template = _template()
    value = _override_defaults(template)[field]

    def clone(*args: Any, **kwargs: Any) -> DummyTemporaryFork:
        pytest.fail("Hardfork.clone() should not run for identical overrides")

    monkeypatch.setattr(Hardfork, "clone", clone)

    with ForkCache() as cache:
        fork = cache.get(template, **{field: value})

    assert fork is template


@pytest.mark.parametrize("field", OVERRIDE_FIELDS)
def test_fork_cache_clones_for_each_changed_blob_override(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    """Clone the template when each blob-related override is changed."""
    template = _template()
    default_value = _override_defaults(template)[field]
    changed_value = type(default_value)(int(default_value) + 1)
    cloned = DummyTemporaryFork()
    seen: dict[str, Any] = {}

    def clone(*args: Any, **kwargs: Any) -> DummyTemporaryFork:
        seen.update(kwargs)
        return cloned

    monkeypatch.setattr(Hardfork, "clone", clone)

    with ForkCache() as cache:
        fork = cache.get(template, **{field: changed_value})

    assert fork is cloned
    assert seen["template"] is template
    assert seen[field] == changed_value


def test_fork_cache_reuses_cached_clone_for_identical_changed_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reuse the same cached clone when override requests repeat."""
    template = _template()
    default_blob_schedule_target = _override_defaults(template)[
        "blob_schedule_target"
    ]
    changed_blob_schedule_target = U64(int(default_blob_schedule_target) + 1)
    cloned = DummyTemporaryFork()
    clone_count = 0

    def clone(*args: Any, **kwargs: Any) -> DummyTemporaryFork:
        del args
        del kwargs
        nonlocal clone_count
        clone_count += 1
        return cloned

    monkeypatch.setattr(Hardfork, "clone", clone)

    with ForkCache() as cache:
        first = cache.get(
            template,
            blob_schedule_target=changed_blob_schedule_target,
        )
        second = cache.get(
            template,
            blob_schedule_target=changed_blob_schedule_target,
        )

    assert first is cloned
    assert second is cloned
    assert first is second
    assert clone_count == 1
