"""Listings of all EIPs, current and upcoming."""

import importlib
import inspect
import pkgutil
import re
from typing import Any

__all__ = []

_prefix = __name__ + "."

ALL_EIPS = []

for _importer, _modname, _ispkg in pkgutil.walk_packages(
    __path__, prefix=_prefix
):
    if not re.search(r"\.eip_\d+$", _modname):
        continue

    _module = importlib.import_module(_modname)

    for _name, _obj in inspect.getmembers(_module, inspect.isclass):
        if re.match(r"^EIP\d+$", _name) and _obj.__module__ == _modname:
            globals()[_name] = _obj
            ALL_EIPS.append(_obj)
            __all__.append(_name)


def __getattr__(name: str) -> Any:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Clean up module namespace
del _importer, _modname, _ispkg, _module, _name, _obj, _prefix
