"""
abstract: Tests [EIP-2930: Access list transaction](https://eips.ethereum.org/EIPS/eip-2930).
Original test by Ori: https://github.com/ethereum/tests/blob/v15.0/src/GeneralStateTestsFiller/stEIP1559/intrinsicGen.js.
"""

from typing import List

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    AccessList,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from ethereum_test_tools import Opcodes as Op

from .spec import ref_spec_2930

REFERENCE_SPEC_GIT_PATH = ref_spec_2930.git_path
REFERENCE_SPEC_VERSION = ref_spec_2930.version

pytestmark = pytest.mark.valid_from("Berlin")

tx_intrinsic_gas_data_vectors = [
    pytest.param(Bytes(b""), id="data_empty"),
    pytest.param(Bytes(b"0x00"), id="data_1_zero_byte"),
    pytest.param(Bytes(b"0x00000000"), id="data_4_zero_byte"),
    pytest.param(Bytes(b"0xFF"), id="data_1_non_zero_byte"),
    pytest.param(Bytes(b"0x00FF"), id="data_1_zero_byte_1_non_zero_byte"),
    pytest.param(Bytes(b"0xFE00"), id="data_1_zero_byte_1_non_zero_byte_reversed"),
    pytest.param(Bytes(b"0x0102030405060708090A0B0C0D0E0F10"), id="data_set_1"),
    pytest.param(
        Bytes(b"0x00010203040506000708090A0B0C0D0E0F10111200131415161718191a1b1c1d1e1f"),
        id="data_set_2",
    ),
    pytest.param(
        Bytes(b"0x0102030405060708090A0B0C0D0E0F101112131415161718191a1b1c1d1e1f20"),
        id="data_set_3",
    ),
    pytest.param(
        Bytes(b"0x01020304050607080910111213141516171819202122232425262728293031"),
        id="data_set_31_bytes",
    ),
    pytest.param(
        Bytes(b"0x000102030405060708090A0B0C0D0E0F101112131415161718191a1b1c1d1e1f"),
        id="data_set_32_bytes",
    ),
    pytest.param(
        Bytes(b"0x010203040506070809101112131415161718192021222324252627282930313233"),
        id="data_set_33_bytes",
    ),
    pytest.param(
        Bytes(b"0x000000000000000000000000000000000000000000000000000000000000000000"),
        id="data_set_33_empty_bytes",
    ),
    pytest.param(
        Bytes(
            b"0x000000000000000000000000000000000000000000000000000000000000000000010203040506070809101112131415161718192021222324252627282930313233"
        ),
        id="data_set_66_bytes_half_zeros",
    ),
]

tx_intrinsic_gas_access_list_vectors = [
    pytest.param([], id="access_list_empty"),
    pytest.param(
        [AccessList(address=1, storage_keys=[])],
        id="access_list_1_address_empty_keys",
    ),
    pytest.param(
        [AccessList(address=1, storage_keys=[0x60A7])],
        id="access_list_1_address_1_keys",
    ),
    pytest.param(
        [AccessList(address=1, storage_keys=[0x60A7, 0x60A8])],
        id="access_list_1_address_2_keys",
    ),
    pytest.param(
        [
            AccessList(address=1, storage_keys=[]),
            AccessList(address=2, storage_keys=[]),
        ],
        id="access_list_2_address_empty_keys",
    ),
    pytest.param(
        [
            AccessList(address=1, storage_keys=[]),
            AccessList(address=2, storage_keys=[0x60A7]),
        ],
        id="access_list_2_address_1_keys",
    ),
    pytest.param(
        [
            AccessList(address=1, storage_keys=[0x60A7]),
            AccessList(address=2, storage_keys=[0x60A8]),
        ],
        id="access_list_2_address_2_keys",
    ),
    pytest.param(
        [
            AccessList(address=1, storage_keys=[0x60A7, 0x60A8]),
            AccessList(address=2, storage_keys=[]),
        ],
        id="access_list_2_address_2_keys_inversion",
    ),
    pytest.param(
        [
            AccessList(address=1, storage_keys=[0xCE11]),
            AccessList(address=2, storage_keys=[0x60A7]),
            *[
                AccessList(
                    address=Address(i),
                    storage_keys=[0x600D, 0x0BAD, 0x60A7, 0xBEEF],
                )
                for i in range(3, 13)  # 3 to 12 inclusive (10 entries)
            ],
        ],
        id="access_list_12_address_42_keys",
    ),
]


@pytest.mark.parametrize("data", tx_intrinsic_gas_data_vectors)
@pytest.mark.parametrize("access_list", tx_intrinsic_gas_access_list_vectors)
@pytest.mark.parametrize(
    "below_intrinsic",
    [
        pytest.param(False),
        pytest.param(True, marks=pytest.mark.exception_test),
    ],
)
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type in [1, 2])
def test_tx_intrinsic_gas(
    state_test: StateTestFiller,
    tx_type: int,
    pre: Alloc,
    fork: Fork,
    data: Bytes,
    access_list: List[AccessList],
    below_intrinsic: bool,
):
    """Transaction intrinsic gas calculation on EIP2930."""
    intrinsic_gas_cost_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas_cost = intrinsic_gas_cost_calculator(calldata=data, access_list=access_list)

    tx = Transaction(
        ty=tx_type,
        sender=pre.fund_eoa(),
        to=pre.deploy_contract(code=Op.SSTORE(0, Op.ADD(1, 1))),
        data=data,
        access_list=access_list,
        gas_limit=intrinsic_gas_cost + (-1 if below_intrinsic else 0),
        error=TransactionException.INTRINSIC_GAS_TOO_LOW if below_intrinsic else None,
        protected=True,
    )

    state_test(env=Environment(), pre=pre, post={}, tx=tx)
