"""Spamoor scenario transaction builders.

This directory is dual-purpose:

- As a *pytest test package* (``tests/benchmark/spamoor``) under the
  execution-specs test tree. The relative imports inside ``test_*.py``
  (``from .helpers import …``, ``from .pool_runner import …``) continue
  to work unchanged.
- As a *standalone pip package* (``eels-spamoor-builders``, declared in
  the sibling ``pyproject.toml``). Downstream tooling that only needs to
  build Spamoor transaction dictionaries (the ``build_*`` helpers return
  unsigned ``dict``\\ s; signing is done downstream — typically via
  ``spamoor_dict_to_transaction``) can ``pip install`` it without
  pulling in the rest of execution-specs:

      pip install git+https://github.com/ethereum/execution-specs.git#subdirectory=tests/benchmark/spamoor
      python -c "from eels_spamoor_builders import build_eoatx_transactions"
"""

from .helpers import (
    build_blob_combined_transactions,
    build_calltx_transactions,
    build_deploytx_transactions,
    build_eoatx_transactions,
    build_erc20_bloater_transactions,
    build_erc20tx_transactions,
    build_evm_fuzz_transactions,
    build_factorydeploytx_transactions,
    build_gasburnertx_transactions,
    build_storagerefundtx_transactions,
    build_storagespam_transactions,
    build_uniswap_swaps_transactions,
)

__all__ = [
    "build_blob_combined_transactions",
    "build_calltx_transactions",
    "build_deploytx_transactions",
    "build_eoatx_transactions",
    "build_erc20_bloater_transactions",
    "build_erc20tx_transactions",
    "build_evm_fuzz_transactions",
    "build_factorydeploytx_transactions",
    "build_gasburnertx_transactions",
    "build_storagerefundtx_transactions",
    "build_storagespam_transactions",
    "build_uniswap_swaps_transactions",
]
