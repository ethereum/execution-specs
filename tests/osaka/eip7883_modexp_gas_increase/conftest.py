"""Shared pytest definitions for EIP-7883 tests."""

from typing import Type

import pytest
from execution_testing import Fork

from ...byzantium.eip198_modexp_precompile.conftest import (  # noqa: F401
    call_contract_post_storage,
    call_opcode,
    call_succeeds,
    exceeds_tx_gas_cap,
    expected_tx_cap_fail,
    gas_measure_contract,
    gas_new,
    gas_old,
    post,
    precompile_gas,
    precompile_gas_modifier,
    total_tx_gas_needed,
    tx,
)
from ...byzantium.eip198_modexp_precompile.spec import ModExpGasSpec
from .spec import modexp_spec_at


@pytest.fixture
def modexp_spec(fork: Fork) -> Type[ModExpGasSpec]:
    """Return the ModExp gas specification in effect at the given fork."""
    return modexp_spec_at(fork)
