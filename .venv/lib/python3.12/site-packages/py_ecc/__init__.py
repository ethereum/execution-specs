import importlib
from importlib.metadata import (
    version as __version,
)
import sys as _sys
from types import (
    ModuleType,
)
from typing import (
    List,
)

_sys.setrecursionlimit(max(100000, _sys.getrecursionlimit()))

__version__ = __version("py_ecc")

_lazy_imports = {
    "bls": "py_ecc.bls",
    "bls12_381": "py_ecc.bls12_381",
    "bn128": "py_ecc.bn128",
    "optimized_bls12_381": "py_ecc.optimized_bls12_381",
    "optimized_bn128": "py_ecc.optimized_bn128",
    "secp256k1": "py_ecc.secp256k1",
}

__all__ = list(_lazy_imports.keys())


def _import_module(name: str) -> ModuleType:
    module = importlib.import_module(_lazy_imports[name])
    globals()[name] = module
    return module


def __getattr__(name: str) -> ModuleType:
    if name in _lazy_imports:
        return _import_module(name)
    raise AttributeError(f"module 'py_ecc' has no attribute '{name}'")


def __dir__() -> List[str]:
    return list(_lazy_imports.keys()) + list(globals().keys())
