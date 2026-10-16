"""Listings of all EIPs for Bogota fork."""

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
        """Typing-only stand-in for Bogota EIP mixins."""

        pass
else:

    def _discover_eips() -> list[type]:
        """
        Collect the ``EIP<n>`` classes defined by this package's
        ``eip_<n>`` modules, in ascending EIP order.

        The package may carry no EIP modules at all, so nothing here
        relies on the discovery loop having run.
        """
        prefix = __name__ + "."
        found = []
        for _importer, modname, ispkg in pkgutil.iter_modules(
            __path__, prefix=prefix
        ):
            if ispkg or not re.search(r"\.eip_\d+$", modname):
                continue

            module = importlib.import_module(modname)

            for name, obj in inspect.getmembers(module, inspect.isclass):
                if re.match(r"^EIP\d+$", name) and obj.__module__ == modname:
                    found.append(obj)

        found.sort(key=lambda cls: int(cls.__name__[3:]))
        return found

    _bogota_eips = _discover_eips()

    class _BogotaEIPsSentinel:
        """Expand to the currently available Bogota EIP mixins."""

        def __mro_entries__(
            self,
            bases: tuple[type, ...],
        ) -> tuple[type, ...]:
            del bases
            return tuple(_bogota_eips)

    BogotaEIPs = _BogotaEIPsSentinel()  # type: ignore[misc]
