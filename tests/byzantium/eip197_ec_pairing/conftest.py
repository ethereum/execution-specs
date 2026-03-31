"""Shared pytest definitions local to EIP-197 tests."""

import pytest
from execution_testing import Fork

from ...common.precompile_fixtures import (
    call_contract_address,  # noqa: F401
    call_contract_code,  # noqa: F401
    call_contract_post_storage,  # noqa: F401
    call_opcode,  # noqa: F401
    call_succeeds,  # noqa: F401
    post,  # noqa: F401
    precompile_gas_modifier,  # noqa: F401
    sender,  # noqa: F401
    tx,  # noqa: F401
    tx_gas_limit,  # noqa: F401
)


@pytest.fixture
def precompile_gas(input_data: bytes, fork: Fork) -> int:
    """Gas cost for the ecpairing precompile."""
    gas_costs = fork.gas_costs()
    k = len(input_data) // 192
    return (
        gas_costs.PRECOMPILE_ECPAIRING_BASE
        + gas_costs.PRECOMPILE_ECPAIRING_PER_POINT * k
    )
