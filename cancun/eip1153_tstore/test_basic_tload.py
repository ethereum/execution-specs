"""
Ethereum Transient Storage EIP Tests
https://eips.ethereum.org/EIPS/eip-1153.
"""

from typing import Dict, Union

import pytest

from ethereum_test_tools import Account, Address, Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .spec import Spec, ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version


@pytest.mark.valid_from("Cancun")
def test_basic_tload_transaction_begin(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Ported .json vectors.

    (01_tloadBeginningTxnFiller.yml)
    load arbitrary value is 0 at beginning of transaction
    """
    slot_tload_at_transaction_begin_result = 1
    slot_code_worked = 2

    address_to = pre.deploy_contract(
        code=Op.JUMPDEST()
        # 01 test
        + Op.SSTORE(slot_tload_at_transaction_begin_result, Op.TLOAD(0))
        + Op.SSTORE(slot_code_worked, 1),
        storage={
            slot_tload_at_transaction_begin_result: 0xFF,
        },
    )

    post = {
        address_to: Account(
            storage={
                slot_tload_at_transaction_begin_result: 0x00,
                slot_code_worked: 0x01,
            }
        )
    }

    tx = Transaction(
        sender=pre.fund_eoa(7_000_000_000_000_000_000),
        to=address_to,
        gas_price=10,
        data=b"",
        gas_limit=5000000,
        value=0,
    )

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Cancun")
def test_basic_tload_works(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Ported .json vectors.

    (02_tloadAfterTstoreFiller.yml)
    tload from same slot after tstore returns correct value
    """
    tstore_value = 88

    slot_tload_after_tstore_result = 0
    slot_tload_after_tstore_result_second_time = 1
    slot_code_worked = 2

    address_to = pre.deploy_contract(
        code=Op.JUMPDEST()
        # 02 test
        + Op.TSTORE(2, tstore_value)
        + Op.SSTORE(slot_tload_after_tstore_result, Op.TLOAD(2))
        + Op.SSTORE(slot_tload_after_tstore_result_second_time, Op.TLOAD(2))
        + Op.SSTORE(slot_code_worked, 1),
        storage={
            slot_tload_after_tstore_result: 0xFF,
            slot_tload_after_tstore_result_second_time: 0xFF,
        },
    )

    post = {
        address_to: Account(
            storage={
                slot_tload_after_tstore_result: tstore_value,
                slot_tload_after_tstore_result_second_time: tstore_value,
                slot_code_worked: 0x01,
            }
        )
    }

    tx = Transaction(
        sender=pre.fund_eoa(7_000_000_000_000_000_000),
        to=address_to,
        gas_price=10,
        data=b"",
        gas_limit=5000000,
        value=0,
    )

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Cancun")
def test_basic_tload_other_after_tstore(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Ported .json vectors.

    (03_tloadAfterStoreIs0Filler.yml)
    Loading any other slot after storing to a slot returns 0.
    """
    tstore_value = 88

    slot_tload_untouched_slot_after_tstore_result = 1
    slot_code_worked = 2

    address_to = pre.deploy_contract(
        code=Op.JUMPDEST()
        # 03 test
        + Op.TSTORE(3, tstore_value)
        + Op.SSTORE(slot_tload_untouched_slot_after_tstore_result, Op.TLOAD(0))
        + Op.SSTORE(slot_code_worked, 1),
        storage={
            slot_tload_untouched_slot_after_tstore_result: 0xFF,
        },
    )

    post = {
        address_to: Account(
            storage={
                slot_tload_untouched_slot_after_tstore_result: 0x00,
                slot_code_worked: 0x01,
            }
        )
    }

    tx = Transaction(
        sender=pre.fund_eoa(7_000_000_000_000_000_000),
        to=address_to,
        gas_price=10,
        data=b"",
        gas_limit=5000000,
        value=0,
    )

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Cancun")
def test_basic_tload_gasprice(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Ported .json vectors.

    (16_tloadGasFiller.yml)
    tload costs 100 gas same as a warm sload
    """
    slot_tload_nonzero_gas_price_result = 1
    slot_tload_zero_gas_price_result = 2
    slot_code_worked = 3

    """
    N         OPNAME       GAS_COST  TOTAL_GAS REMAINING_GAS     STACK
    28-1         MSTORE         2     20748   4958252    2:[4ba82f,0,]
                 MSTORE [0] = 4958255
    29-1          PUSH1         3     20754   4958246
    30-1          TLOAD       100     20757   4958243    1:[10,]
    31-1            GAS         2     20857   4958143    1:[2,]
    32-1          PUSH1         3     20859   4958141    2:[2,4ba7bd,]
    33-1         MSTORE         6     20862   4958138    3:[2,4ba7bd,20,]
                 MSTORE [32] = 4958141
    """
    extra_opcode_gas = 11  # mstore(3), push1(3),gas(2),push1(3)

    address_to = pre.deploy_contract(
        code=Op.JUMPDEST()
        # 16 test
        + Op.TSTORE(16, 2)
        + Op.MSTORE(0, Op.GAS())  # hot load the memory to make the extra_opcode_gas be 11
        + Op.MSTORE(0, Op.GAS())
        + Op.TLOAD(16)
        + Op.MSTORE(32, Op.GAS())
        + Op.SSTORE(slot_tload_nonzero_gas_price_result, Op.SUB(Op.MLOAD(0), Op.MLOAD(32)))
        + Op.SSTORE(
            slot_tload_nonzero_gas_price_result,
            Op.SUB(Op.SLOAD(slot_tload_nonzero_gas_price_result), extra_opcode_gas),
        )
        + Op.MSTORE(0, Op.GAS())
        + Op.TLOAD(5)  # tload slot at 5 is 0
        + Op.MSTORE(32, Op.GAS())
        + Op.SSTORE(slot_tload_zero_gas_price_result, Op.SUB(Op.MLOAD(0), Op.MLOAD(32)))
        + Op.SSTORE(
            slot_tload_zero_gas_price_result,
            Op.SUB(Op.SLOAD(slot_tload_zero_gas_price_result), extra_opcode_gas),
        )
        + Op.SSTORE(slot_code_worked, 1),
        storage={
            slot_tload_nonzero_gas_price_result: 0xFF,
            slot_tload_zero_gas_price_result: 0xFF,
        },
    )

    post = {
        address_to: Account(
            storage={
                slot_tload_nonzero_gas_price_result: Spec.TLOAD_GAS_COST,
                slot_tload_zero_gas_price_result: Spec.TLOAD_GAS_COST,
                slot_code_worked: 0x01,
            }
        )
    }

    tx = Transaction(
        sender=pre.fund_eoa(7_000_000_000_000_000_000),
        to=address_to,
        gas_price=10,
        data=b"",
        gas_limit=5000000,
        value=0,
    )

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Cancun")
def test_basic_tload_after_store(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Ported .json vectors.

    (18_tloadAfterStoreFiller.yml)
    tload from same slot after store returns 0
    """
    slot_tload_from_sstore_result = 1
    slot_code_worked = 2

    address_to = pre.deploy_contract(
        code=Op.JUMPDEST()
        # 18 test
        + Op.SSTORE(slot_tload_from_sstore_result, 22)
        + Op.SSTORE(slot_tload_from_sstore_result, Op.TLOAD(slot_tload_from_sstore_result))
        + Op.SSTORE(slot_code_worked, 1),
        storage={
            slot_tload_from_sstore_result: 0xFF,
        },
    )

    post: Dict[Address, Union[Account, object]] = {}
    post[address_to] = Account(
        storage={
            slot_tload_from_sstore_result: 0x00,
            slot_code_worked: 0x01,
        }
    )

    tx = Transaction(
        sender=pre.fund_eoa(7_000_000_000_000_000_000),
        to=address_to,
        gas_price=10,
        data=b"",
        gas_limit=5000000,
        value=0,
    )

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
