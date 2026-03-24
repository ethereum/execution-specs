"""Test the pre-allocation methods in the filler module."""

import pytest

from execution_testing.base_types import Account, Address
from execution_testing.forks import Fork, Prague
from execution_testing.vm import Op

from ...shared.pre_alloc import AllocFlags
from ..pre_alloc import Alloc


def create_test_alloc(
    flags: AllocFlags = AllocFlags.MUTABLE,
    fork: Fork = Prague,
) -> Alloc:
    """Create a test Alloc instance with default iterators."""
    return Alloc(
        flags=flags,
        fork=fork,
    )


def test_alloc_deploy_contract_basic() -> None:
    """Test basic `Alloc.deploy_contract` functionality."""
    pre_1 = create_test_alloc()
    pre_2 = create_test_alloc()

    contract_code_a = Op.SSTORE(0, 1) + Op.STOP
    contract_code_b = Op.SSTORE(0, 2) + Op.STOP

    contract_1_a_1 = pre_1.deploy_contract(contract_code_a)
    contract_1_a_2 = pre_1.deploy_contract(contract_code_a)
    contract_1_b = pre_1.deploy_contract(contract_code_b)

    # Contracts should be deployed to different addresses
    assert contract_1_a_1 != contract_1_a_2
    assert contract_1_b != contract_1_a_1
    assert contract_1_b != contract_1_a_2
    assert contract_1_a_1 in pre_1
    assert contract_1_a_2 in pre_1
    assert contract_1_a_1 not in pre_2

    # Check accounts exist and have code
    pre_contract_1_a_1_account = pre_1[contract_1_a_1]
    pre_contract_1_a_2_account = pre_1[contract_1_a_2]
    assert pre_contract_1_a_1_account is not None
    assert pre_contract_1_a_2_account is not None
    assert pre_contract_1_a_1_account.code is not None
    assert pre_contract_1_a_2_account.code is not None
    assert len(pre_contract_1_a_1_account.code) > 0
    assert len(pre_contract_1_a_2_account.code) > 0

    # Deploy contracts in second pre, verify addresses
    contract_2_a_1 = pre_2.deploy_contract(contract_code_a)
    contract_2_a_2 = pre_2.deploy_contract(contract_code_a)
    contract_2_b = pre_2.deploy_contract(contract_code_b)

    assert contract_1_a_1 == contract_2_a_1
    assert contract_1_a_2 == contract_2_a_2
    assert contract_1_b == contract_2_b


def test_alloc_deploy_contract_with_balance() -> None:
    """Test `Alloc.deploy_contract` with balance."""
    pre = create_test_alloc()
    balance = 10**18
    contract_with_balance_1 = pre.deploy_contract(Op.STOP, balance=balance)
    contract_with_balance_2 = pre.deploy_contract(Op.STOP, balance=balance)
    contract_without_balance = pre.deploy_contract(Op.STOP, balance=0)
    assert contract_with_balance_1 != contract_without_balance
    assert contract_with_balance_1 != contract_with_balance_2

    assert contract_with_balance_1 in pre
    account = pre[contract_with_balance_1]
    assert account is not None
    assert account.balance == balance

    # Redeploy in another pre
    pre_2 = create_test_alloc()
    assert contract_with_balance_1 == pre_2.deploy_contract(
        Op.STOP, balance=balance
    )
    assert contract_with_balance_2 == pre_2.deploy_contract(
        Op.STOP, balance=balance
    )


def test_alloc_deploy_contract_with_storage() -> None:
    """Test `Alloc.deploy_contract` with storage."""
    pre = create_test_alloc()
    storage_a = {0: 42, 1: 100}
    contract_with_storage_1 = pre.deploy_contract(
        Op.STOP,
        storage=storage_a,  # type: ignore
    )
    contract_with_storage_2 = pre.deploy_contract(
        Op.STOP,
        storage=storage_a,  # type: ignore
    )
    contract_without_storage = pre.deploy_contract(Op.STOP, storage={})
    assert contract_with_storage_1 != contract_without_storage
    assert contract_with_storage_1 != contract_with_storage_2

    assert contract_with_storage_1 in pre
    account = pre[contract_with_storage_1]
    assert account is not None
    assert account.storage is not None
    assert account.storage[0] == storage_a[0]
    assert account.storage[1] == storage_a[1]

    # Redeploy in another pre
    pre_2 = create_test_alloc()
    assert contract_with_storage_1 == pre_2.deploy_contract(
        Op.STOP,
        storage=storage_a,  # type: ignore
    )
    assert contract_with_storage_2 == pre_2.deploy_contract(
        Op.STOP,
        storage=storage_a,  # type: ignore
    )


def test_alloc_fund_eoa_basic() -> None:
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


def test_alloc_nonexistent_account() -> None:
    """Test `Alloc.nonexistent_account` returns a nonexistent address."""
    pre = create_test_alloc()
    addr_1 = pre.nonexistent_account()
    addr_2 = pre.nonexistent_account()

    assert isinstance(addr_1, Address)
    # The address must not be in the pre-state (nonexistent account).
    assert addr_1 not in pre
    assert addr_2 not in pre
    # Each call returns a unique address.
    assert addr_1 != addr_2


def test_alloc_deploy_contract_code_types() -> None:
    """Test `Alloc.deploy_contract` bytecode output."""
    pre = create_test_alloc()

    contract = pre.deploy_contract(Op.SSTORE(0, 1) + Op.STOP)

    assert contract in pre
    account = pre[contract]
    assert account is not None
    assert account.code is not None

    # Bytecode should be raw opcodes
    assert account.code == bytes.fromhex("600160005500")


@pytest.mark.parametrize("flags", [AllocFlags.NONE, AllocFlags.MUTABLE])
def test_alloc_flags(flags: AllocFlags) -> None:
    """Test different allocation modes."""
    pre = create_test_alloc(flags=flags)

    assert pre._flags == flags

    # Test that we can deploy contracts regardless of mode
    contract = pre.deploy_contract(Op.STOP)
    assert contract in pre


def test_alloc_flag_allow_account_address_set() -> None:
    """
    Test that setting a hard-coded address to an account only works
    when mutable.
    """
    # With flag: should allow setting accounts directly
    pre_with_flag = create_test_alloc(flags=AllocFlags.MUTABLE)
    address = Address(0x1234567890123456789012345678901234567890)

    pre_with_flag[address] = Account(balance=100)
    assert address in pre_with_flag

    # Without flag: should raise
    pre_without_flag = create_test_alloc(flags=AllocFlags.NONE)
    with pytest.raises(ValueError, match="Cannot set items in immutable mode"):
        pre_without_flag[address] = Account(balance=100)


def test_alloc_flag_allow_deploy_to_hardcoded_address() -> None:
    """Test that deploying to hardcoded addresses requires MUTABLE flag."""
    # With flag: should allow deploying to hardcoded address
    pre_with_flag = create_test_alloc(flags=AllocFlags.MUTABLE)
    hardcoded_address = Address(0xDEADBEEFDEADBEEFDEADBEEFDEADBEEFDEADBEEF)
    contract = pre_with_flag.deploy_contract(
        Op.STOP, address=hardcoded_address
    )
    assert contract == hardcoded_address
    assert contract in pre_with_flag

    # Without flag: should raise
    pre_without_flag = create_test_alloc(flags=AllocFlags.NONE)
    with pytest.raises(ValueError, match="Cannot set items in immutable mode"):
        pre_without_flag.deploy_contract(Op.STOP, address=hardcoded_address)


def test_alloc_flag_allow_zero_nonce_contracts() -> None:
    """Test that deploying contracts with zero nonce requires MUTABLE flag."""
    # With flag: should allow deploying contracts with nonce 0
    pre_with_flag = create_test_alloc(flags=AllocFlags.MUTABLE)
    contract = pre_with_flag.deploy_contract(Op.STOP, nonce=0)
    assert contract in pre_with_flag
    account = pre_with_flag[contract]
    assert account is not None
    assert account.nonce == 0

    # Without flag: should raise
    pre_without_flag = create_test_alloc(flags=AllocFlags.NONE)
    with pytest.raises(ValueError, match="Cannot set items in immutable mode"):
        pre_without_flag.deploy_contract(Op.STOP, nonce=0)


def test_alloc_mutable_flag_combines_permissions() -> None:
    """Test that MUTABLE flag includes multiple permissions."""
    pre = create_test_alloc(flags=AllocFlags.MUTABLE)

    # Should allow account address set
    address = Address(0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA)

    pre[address] = Account(balance=100)
    assert address in pre

    # Should allow deploying to hardcoded address
    hardcoded_address = Address(0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB)
    contract = pre.deploy_contract(Op.STOP, address=hardcoded_address)
    assert contract == hardcoded_address

    # Should allow zero nonce contracts
    zero_nonce_contract = pre.deploy_contract(Op.STOP, nonce=0)
    assert zero_nonce_contract in pre
    account = pre[zero_nonce_contract]
    assert account is not None
    assert account.nonce == 0


def test_global_address_allocation_consistency() -> None:
    """Test that address allocation produces consistent results."""
    # Create two alloc instances with same parameters
    pre_1 = create_test_alloc()
    pre_2 = create_test_alloc()

    # Deploy contracts and check they get the same addresses
    contract_1_pre_1 = pre_1.deploy_contract(Op.STOP)
    contract_1_pre_2 = pre_2.deploy_contract(Op.STOP)

    # Should get same starting address
    assert contract_1_pre_1 == contract_1_pre_2

    # Second contracts should also match
    contract_2_pre_1 = pre_1.deploy_contract(Op.STOP)
    contract_2_pre_2 = pre_2.deploy_contract(Op.STOP)

    assert contract_2_pre_1 == contract_2_pre_2

    # Third contract, when distinct, should not match
    contract_3_pre_1 = pre_1.deploy_contract(Op.INVALID)
    contract_3_pre_2 = pre_2.deploy_contract(Op.STOP)

    assert contract_3_pre_1 != contract_3_pre_2


def test_alloc_deploy_contract_nonce() -> None:
    """Test that deployed contracts have correct nonce."""
    pre = create_test_alloc()

    contract = pre.deploy_contract(Op.STOP)
    account = pre[contract]

    assert account is not None
    assert account.nonce == 1  # Deployed contracts should have nonce 1


def test_alloc_fund_eoa_returns_eoa_object() -> None:
    """Test that fund_eoa returns proper EOA object with private key access."""
    pre = create_test_alloc()

    eoa = pre.fund_eoa()

    # Should be able to access private key (EOA object)
    assert hasattr(eoa, "key")
    assert eoa.key is not None

    # Should also be in pre-allocation
    assert eoa in pre
    account = pre[eoa]
    assert account is not None
    assert account.balance == pre._eoa_fund_amount_default
