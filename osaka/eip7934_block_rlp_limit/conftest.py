"""Fixtures for the EIP-7934 RLP block size limit tests."""

import pytest

from ethereum_test_tools import (
    EOA,
    Address,
    Alloc,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types import Environment


@pytest.fixture
def post() -> Alloc:
    """Post state allocation fixture."""
    return Alloc()


@pytest.fixture
def env() -> Environment:
    """Environment fixture with a specified gas limit."""
    return Environment(gas_limit=100_000_000)


@pytest.fixture
def sender(pre: Alloc) -> EOA:
    """Funded EOA fixture used for sending transactions."""
    return pre.fund_eoa()


@pytest.fixture
def contract_recipient(pre: Alloc) -> Address:
    """Deploy a simple contract that can receive large calldata."""
    contract_code = Op.SSTORE(0, Op.CALLDATASIZE) + Op.STOP
    return pre.deploy_contract(contract_code)
