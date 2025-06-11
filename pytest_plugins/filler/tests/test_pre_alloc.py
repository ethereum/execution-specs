"""Test the pre-allocation methods in the filler module."""

from itertools import count

import pytest

from ethereum_test_base_types import Address, TestPrivateKey, TestPrivateKey2
from ethereum_test_types import EOA
from ethereum_test_vm import EVMCodeType
from ethereum_test_vm import Opcodes as Op

from ..pre_alloc import (
    CONTRACT_ADDRESS_INCREMENTS_DEFAULT,
    CONTRACT_START_ADDRESS_DEFAULT,
    Alloc,
    AllocMode,
)


def create_test_alloc(
    alloc_mode: AllocMode = AllocMode.PERMISSIVE, evm_code_type: EVMCodeType = EVMCodeType.LEGACY
) -> Alloc:
    """Create a test Alloc instance with default iterators."""
    contract_iter = iter(
        Address(CONTRACT_START_ADDRESS_DEFAULT + (i * CONTRACT_ADDRESS_INCREMENTS_DEFAULT))
        for i in count()
    )
    eoa_iter = iter(
        EOA(key=TestPrivateKey + i if i != 1 else TestPrivateKey2, nonce=0).copy() for i in count()
    )

    return Alloc(
        alloc_mode=alloc_mode,
        contract_address_iterator=contract_iter,
        eoa_iterator=eoa_iter,
        evm_code_type=evm_code_type,
    )


def test_alloc_deploy_contract_basic():
    """Test basic `Alloc.deploy_contract` functionality."""
    pre = create_test_alloc()

    contract_1 = pre.deploy_contract(Op.SSTORE(0, 1) + Op.STOP)
    contract_2 = pre.deploy_contract(Op.SSTORE(0, 2) + Op.STOP)

    # Contracts should be deployed to different addresses
    assert contract_1 != contract_2
    assert contract_1 in pre
    assert contract_2 in pre

    # Check that addresses follow expected pattern
    assert contract_1 == Address(CONTRACT_START_ADDRESS_DEFAULT)
    assert contract_2 == Address(
        CONTRACT_START_ADDRESS_DEFAULT + CONTRACT_ADDRESS_INCREMENTS_DEFAULT
    )

    # Check accounts exist and have code
    pre_contract_1_account = pre[contract_1]
    pre_contract_2_account = pre[contract_2]
    assert pre_contract_1_account is not None
    assert pre_contract_2_account is not None
    assert pre_contract_1_account.code is not None
    assert pre_contract_2_account.code is not None
    assert len(pre_contract_1_account.code) > 0
    assert len(pre_contract_2_account.code) > 0


def test_alloc_deploy_contract_with_balance():
    """Test `Alloc.deploy_contract` with balance."""
    pre = create_test_alloc()
    balance = 10**18
    contract = pre.deploy_contract(Op.STOP, balance=balance)

    assert contract in pre
    account = pre[contract]
    assert account is not None
    assert account.balance == balance


def test_alloc_deploy_contract_with_storage():
    """Test `Alloc.deploy_contract` with storage."""
    pre = create_test_alloc()
    storage = {0: 42, 1: 100}
    contract = pre.deploy_contract(Op.STOP, storage=storage)

    assert contract in pre
    account = pre[contract]
    assert account is not None
    assert account.storage is not None
    assert account.storage[0] == 42
    assert account.storage[1] == 100


def test_alloc_fund_eoa_basic():
    """Test basic `Alloc.fund_eoa` functionality."""
    pre = create_test_alloc()

    eoa_1 = pre.fund_eoa(10**18)
    eoa_2 = pre.fund_eoa(2 * 10**18)

    # EOAs should be different
    assert eoa_1 != eoa_2
    assert eoa_1 in pre
    assert eoa_2 in pre

    # Check balances
    account_1 = pre[eoa_1]
    account_2 = pre[eoa_2]
    assert account_1 is not None
    assert account_2 is not None
    assert account_1.balance == 10**18
    assert account_2.balance == 2 * 10**18


def test_alloc_fund_address():
    """Test `Alloc.fund_address` functionality."""
    pre = create_test_alloc()
    address = Address(0x1234567890123456789012345678901234567890)
    amount = 5 * 10**18

    pre.fund_address(address, amount)

    assert address in pre
    account = pre[address]
    assert account is not None
    assert account.balance == amount


def test_alloc_empty_account():
    """Test `Alloc.empty_account` functionality."""
    pre = create_test_alloc()
    empty_addr = pre.empty_account()

    # Check that we get a valid address (address generation works)
    assert isinstance(empty_addr, Address)
    # Note: empty_account() only returns address, doesn't add to pre


@pytest.mark.parametrize("evm_code_type", [EVMCodeType.LEGACY, EVMCodeType.EOF_V1])
def test_alloc_deploy_contract_code_types(evm_code_type: EVMCodeType):
    """Test `Alloc.deploy_contract` with different EVM code types."""
    pre = create_test_alloc(evm_code_type=evm_code_type)

    contract = pre.deploy_contract(Op.SSTORE(0, 1) + Op.STOP)

    assert contract in pre
    account = pre[contract]
    assert account is not None
    assert account.code is not None

    if evm_code_type == EVMCodeType.LEGACY:
        # Legacy bytecode should be raw opcodes
        assert account.code == bytes.fromhex("600160005500")
    elif evm_code_type == EVMCodeType.EOF_V1:
        # EOF v1 should have the EOF container header
        assert account.code.startswith(b"\xef\x00\x01")


@pytest.mark.parametrize("alloc_mode", [AllocMode.STRICT, AllocMode.PERMISSIVE])
def test_alloc_modes(alloc_mode: AllocMode):
    """Test different allocation modes."""
    pre = create_test_alloc(alloc_mode=alloc_mode)

    assert pre._alloc_mode == alloc_mode

    # Test that we can deploy contracts regardless of mode
    contract = pre.deploy_contract(Op.STOP)
    assert contract in pre


def test_global_address_allocation_consistency():
    """Test that address allocation produces consistent results."""
    # Create two alloc instances with same parameters
    pre1 = create_test_alloc()
    pre2 = create_test_alloc()

    # Deploy contracts and check they get the same addresses
    contract1_pre1 = pre1.deploy_contract(Op.STOP)
    contract1_pre2 = pre2.deploy_contract(Op.STOP)

    # Should get same starting address
    assert contract1_pre1 == contract1_pre2
    assert contract1_pre1 == Address(CONTRACT_START_ADDRESS_DEFAULT)

    # Second contracts should also match
    contract2_pre1 = pre1.deploy_contract(Op.STOP)
    contract2_pre2 = pre2.deploy_contract(Op.STOP)

    assert contract2_pre1 == contract2_pre2
    assert contract2_pre1 == Address(
        CONTRACT_START_ADDRESS_DEFAULT + CONTRACT_ADDRESS_INCREMENTS_DEFAULT
    )


def test_alloc_deploy_contract_nonce():
    """Test that deployed contracts have correct nonce."""
    pre = create_test_alloc()

    contract = pre.deploy_contract(Op.STOP)
    account = pre[contract]

    assert account is not None
    assert account.nonce == 1  # Deployed contracts should have nonce 1


def test_alloc_fund_eoa_returns_eoa_object():
    """Test that fund_eoa returns proper EOA object with private key access."""
    pre = create_test_alloc()

    eoa = pre.fund_eoa(10**18)

    # Should be able to access private key (EOA object)
    assert hasattr(eoa, "key")
    assert eoa.key is not None

    # Should also be in pre-allocation
    assert eoa in pre
    account = pre[eoa]
    assert account is not None
    assert account.balance == 10**18


def test_alloc_multiple_contracts_sequential_addresses():
    """Test that multiple contracts get sequential addresses."""
    pre = create_test_alloc()

    contracts = []
    for i in range(5):
        contract = pre.deploy_contract(Op.PUSH1(i) + Op.STOP)
        contracts.append(contract)

    # Check addresses are sequential
    for i, contract in enumerate(contracts):
        expected_addr = Address(
            CONTRACT_START_ADDRESS_DEFAULT + (i * CONTRACT_ADDRESS_INCREMENTS_DEFAULT)
        )
        assert contract == expected_addr
        assert contract in pre
