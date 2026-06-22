"""Listings of all EIPs for Bogotá fork."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from execution_testing.forks.base_fork import BaseFork

__all__ = ["BogotaEIPs"]

if TYPE_CHECKING:

    class BogotaEIPs(BaseFork):
        """Typing-only stand-in for Bogotá EIP mixins."""

        pass
else:
    _prefix = __name__ + "."
    _bogota_eips = []

    for _importer, _modname, _ispkg in pkgutil.iter_modules(
        __path__, prefix=_prefix
    ):
        if _ispkg or not re.search(r"\.eip_\d+$", _modname):
            continue

        _module = importlib.import_module(_modname)

        for _name, _obj in inspect.getmembers(_module, inspect.isclass):
            if re.match(r"^EIP\d+$", _name) and _obj.__module__ == _modname:
                _bogota_eips.append(_obj)

    _bogota_eips.sort(key=lambda cls: int(cls.__name__[3:]))

    class _BogotaEIPsSentinel:
        """Expand to the currently available Bogotá EIP mixins."""

        def __mro_entries__(
            self,
            bases: tuple[type, ...],
        ) -> tuple[type, ...]:
            del bases
            return tuple(_bogota_eips)

    BogotaEIPs = _BogotaEIPsSentinel()  # type: ignore[misc]

    del _importer, _ispkg, _modname, _module, _name, _obj, _prefix
