"""
Test the pre-allocation methods in the filler module.
"""

import pytest

from ethereum_test_base_types import Address, TestAddress, TestAddress2
from ethereum_test_vm import EVMCodeType
from ethereum_test_vm import Opcodes as Op

from ..pre_alloc import (
    CONTRACT_ADDRESS_INCREMENTS_DEFAULT,
    CONTRACT_START_ADDRESS_DEFAULT,
    Alloc,
    AllocMode,
    contract_address_iterator,
    eoa_iterator,
    pre,
)

globals()["pre"] = pre
globals()["contract_address_iterator"] = contract_address_iterator
globals()["eoa_iterator"] = eoa_iterator

pytestmark = [
    pytest.mark.parametrize("alloc_mode", [AllocMode.STRICT, AllocMode.PERMISSIVE]),
    pytest.mark.parametrize("contract_start_address", [CONTRACT_START_ADDRESS_DEFAULT]),
    pytest.mark.parametrize("contract_address_increments", [CONTRACT_ADDRESS_INCREMENTS_DEFAULT]),
    pytest.mark.parametrize("evm_code_type", [EVMCodeType.LEGACY, EVMCodeType.EOF_V1]),
]


def test_alloc_deploy_contract(pre: Alloc, evm_code_type: EVMCodeType):
    """
    Test `Alloc.deploy_contract` functionallity.
    """
    contract_1 = pre.deploy_contract(Op.SSTORE(0, 1) + Op.STOP)
    contract_2 = pre.deploy_contract(Op.SSTORE(0, 2) + Op.STOP)
    assert contract_1 == Address(CONTRACT_START_ADDRESS_DEFAULT)
    assert contract_2 == Address(
        CONTRACT_START_ADDRESS_DEFAULT + CONTRACT_ADDRESS_INCREMENTS_DEFAULT
    )
    assert contract_1 in pre
    assert contract_2 in pre
    pre_contract_1_account = pre[contract_1]
    pre_contract_2_account = pre[contract_2]
    assert pre_contract_1_account is not None
    assert pre_contract_2_account is not None
    if evm_code_type == EVMCodeType.LEGACY:
        assert pre_contract_1_account.code == bytes.fromhex("600160005500")
        assert pre_contract_2_account.code == bytes.fromhex("600260005500")
    elif evm_code_type == EVMCodeType.EOF_V1:
        assert pre_contract_1_account.code == (
            b"\xef\x00\x01\x01\x00\x04\x02\x00\x01\x00\x06\x04\x00\x00\x00\x00\x80\x00"
            + b"\x02`\x01`\x00U\x00"
        )
        assert pre_contract_2_account.code == (
            b"\xef\x00\x01\x01\x00\x04\x02\x00\x01\x00\x06\x04\x00\x00\x00\x00\x80\x00"
            + b"\x02`\x02`\x00U\x00"
        )


def test_alloc_fund_sender(pre: Alloc):
    """
    Test `Alloc.fund_eoa` functionallity.
    """
    sender_1 = pre.fund_eoa(10**18)
    sender_2 = pre.fund_eoa(10**18)
    assert sender_1 != sender_2
    assert sender_1 in pre
    assert sender_2 in pre
    assert Address(sender_1) == TestAddress
    assert Address(sender_2) == TestAddress2
    pre_sender_1 = pre[sender_1]
    pre_sender_2 = pre[sender_2]
    assert pre_sender_1 is not None
    assert pre_sender_2 is not None
    assert pre_sender_1.balance == 10**18
    assert pre_sender_2.balance == 10**18
