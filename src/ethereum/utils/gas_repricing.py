"""Shared gas repricing config loader and spec-side applier."""

import json
import os
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

_ENV_VAR = "EELS_GAS_REPRICING_CONFIG"


@lru_cache(maxsize=1)
def load_repricing_config() -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Load gas repricing overrides from JSON config.

    Return None if env var is unset or empty.
    """
    config_path = os.environ.get(_ENV_VAR, "")
    if not config_path:
        return None

    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(
            f"{_ENV_VAR} points to non-existent file: {config_path}"
        )

    with open(path) as f:
        config = json.load(f)

    warnings.warn(
        f"Gas repricing config loaded from {config_path}",
        stacklevel=2,
    )
    return config


def apply_spec_repricing(
    fork_name: str,
    module_globals: dict,
) -> None:
    """
    Apply repricing overrides to module globals.

    Mutates module_globals in place, preserving the
    original type wrapper (Uint, U64, etc.).
    """
    config = load_repricing_config()
    if config is None:
        return

    overrides = config.get(fork_name)
    if overrides is None:
        return

    for name, value in overrides.items():
        if name not in module_globals:
            raise ValueError(
                f"Unknown gas constant '{name}' "
                f"in repricing config for fork "
                f"'{fork_name}'."
            )
        original = module_globals[name]
        module_globals[name] = type(original)(value)
