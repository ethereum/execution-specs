"""
abstract: Tests [EIP-1153: Transient Storage Opcodes](https://eips.ethereum.org/EIPS/eip-1153)

    Test [EIP-1153: Transient Storage Opcodes](https://eips.ethereum.org/EIPS/eip-1153). Ports
    and extends some tests from
    [ethereum/tests/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage)
"""  # noqa: E501

# from typing import Mapping

import pytest

from ethereum_test_tools import Account, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, TestAddress, Transaction

from .spec import ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version

pytestmark = [pytest.mark.valid_from("Cancun")]

code_address = 0x100


def test_transient_storage_unset_values(state_test: StateTestFiller):
    """
    Test that tload returns zero for unset values. Loading an arbitrary value is
    0 at beginning of transaction: TLOAD(x) is 0.

    Based on [ethereum/tests/.../01_tloadBeginningTxnFiller.yml](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/01_tloadBeginningTxnFiller.yml)",  # noqa: E501
    """
    env = Environment()

    slots_under_test = [0, 1, 2, 2**128, 2**256 - 1]
    code = b"".join([Op.SSTORE(slot, Op.TLOAD(slot)) for slot in slots_under_test])

    pre = {
        TestAddress: Account(balance=10_000_000),
        code_address: Account(code=code, storage={slot: 1 for slot in slots_under_test}),
    }

    txs = [
        Transaction(
            to=code_address,
            data=b"",
            gas_limit=1_000_000,
        )
    ]

    post = {code_address: Account(storage={slot: 0 for slot in slots_under_test})}

    state_test(
        env=env,
        pre=pre,
        post=post,
        txs=txs,
    )


def test_tload_after_tstore(state_test: StateTestFiller):
    """
    Loading after storing returns the stored value: TSTORE(x, y), TLOAD(x)
    returns y.

    Based on [ethereum/tests/.../02_tloadAfterTstoreFiller.yml](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/02_tloadAfterTstoreFiller.yml)",  # noqa: E501
    """
    env = Environment()

    slots_under_test = [0, 1, 2, 2**128, 2**256 - 1]
    code = b"".join(
        [Op.TSTORE(slot, slot) + Op.SSTORE(slot, Op.TLOAD(slot)) for slot in slots_under_test]
    )

    pre = {
        TestAddress: Account(balance=10_000_000),
        code_address: Account(code=code, storage={slot: 0 for slot in slots_under_test}),
    }

    txs = [
        Transaction(
            to=code_address,
            data=b"",
            gas_limit=1_000_000,
        )
    ]

    post = {code_address: Account(storage={slot: slot for slot in slots_under_test})}

    state_test(
        env=env,
        pre=pre,
        post=post,
        txs=txs,
    )


def test_tload_after_tstore_is_zero(state_test: StateTestFiller):
    """
    Test that tload returns zero after tstore is called with zero.

    Based on [ethereum/tests/.../03_tloadAfterStoreIs0Filler.yml](https://github.com/ethereum/tests/blob/9b00b68593f5869eb51a6659e1cc983e875e616b/src/EIPTestsFiller/StateTests/stEIP1153-transientStorage/03_tloadAfterStoreIs0Filler.yml)",  # noqa: E501
    """
    env = Environment()

    slots_to_write = [1, 4, 2**128, 2**256 - 2]
    slots_to_read = [slot - 1 for slot in slots_to_write] + [slot + 1 for slot in slots_to_write]
    assert set.intersection(set(slots_to_write), set(slots_to_read)) == set()

    code = b"".join([Op.TSTORE(slot, 1234) for slot in slots_to_write]) + b"".join(
        [Op.SSTORE(slot, Op.TLOAD(slot)) for slot in slots_to_read]
    )

    pre = {
        TestAddress: Account(balance=10_000_000),
        code_address: Account(
            code=code, storage={slot: 0xFFFF for slot in slots_to_write + slots_to_read}
        ),
    }

    txs = [
        Transaction(
            to=code_address,
            data=b"",
            gas_limit=1_000_000,
        )
    ]

    post = {
        code_address: Account(
            storage={slot: 0 for slot in slots_to_read} | {slot: 0xFFFF for slot in slots_to_write}
        )
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        txs=txs,
    )
