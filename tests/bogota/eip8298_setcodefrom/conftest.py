"""Fixtures for the EIP-8298 `SETCODEFROM` tests."""

import pytest
from execution_testing import Address, Alloc

from .helpers import (
    RESULT_SLOT,
    SENTINEL,
    SHELL_CODE,
    TEMPLATE_B_CODE,
    TEMPLATE_CODE,
)


@pytest.fixture
def template(pre: Alloc) -> Address:
    """Deploy a valid source that writes `TEMPLATE_MARKER`."""
    return pre.deploy_contract(TEMPLATE_CODE)


@pytest.fixture
def template_b(pre: Alloc) -> Address:
    """Deploy a second valid source that writes `TEMPLATE_B_MARKER`."""
    return pre.deploy_contract(TEMPLATE_B_CODE)


@pytest.fixture
def shell(pre: Alloc) -> Address:
    """Deploy a `SHELL_CODE` adopter with `RESULT_SLOT` set to `SENTINEL`."""
    return pre.deploy_contract(SHELL_CODE, storage={RESULT_SLOT: SENTINEL})


@pytest.fixture
def shell_twin(pre: Alloc) -> Address:
    """Deploy a second `SHELL_CODE` account, a same-hash source for `shell`."""
    return pre.deploy_contract(SHELL_CODE)
