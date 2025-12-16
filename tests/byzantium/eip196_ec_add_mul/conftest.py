"""Shared pytest definitions local to EIP-196 tests."""

import pytest
from execution_testing import (
    Address,
    Fork,
)

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
from .spec import Spec


@pytest.fixture
def precompile_gas(precompile_address: Address, fork: Fork) -> int:
    """Gas cost for the precompile."""
    gas_costs = fork.gas_costs()
    match precompile_address:
        case Spec.ECADD:
            return gas_costs.G_PRECOMPILE_ECADD
        case Spec.ECMUL:
            return gas_costs.G_PRECOMPILE_ECMUL
        case _:
            raise ValueError(
                f"Unexpected precompile address: {precompile_address}"
            )
