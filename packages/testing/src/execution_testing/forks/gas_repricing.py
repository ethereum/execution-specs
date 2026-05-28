"""Gas repricing override loader for fast iteration on gas schedules."""

from dataclasses import fields, replace

from ethereum.utils.gas_repricing import load_repricing_config

from .gas_costs import GasCosts

_VALID_FIELDS = frozenset(f.name for f in fields(GasCosts))


def _validate_overrides(
    fork_name: str,
    overrides: dict,
) -> None:
    for field_name, value in overrides.items():
        if field_name not in _VALID_FIELDS:
            raise ValueError(
                f"Unknown GasCosts field '{field_name}' "
                f"in repricing config for fork "
                f"'{fork_name}'. "
                f"Valid fields: {sorted(_VALID_FIELDS)}"
            )
        if not isinstance(value, int):
            raise TypeError(
                f"GasCosts field '{field_name}' for fork "
                f"'{fork_name}' must be of type int, "
                f"got {type(value).__name__}: {value!r}"
            )


def apply_repricing(fork_name: str, base_costs: GasCosts) -> GasCosts:
    """Apply repricing overrides for fork_name to base_costs."""
    config = load_repricing_config()
    if config is None:
        return base_costs

    overrides = config.get(fork_name)
    if overrides is None:
        return base_costs

    _validate_overrides(fork_name, overrides)
    return replace(base_costs, **overrides)
