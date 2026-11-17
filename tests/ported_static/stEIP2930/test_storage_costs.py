"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP2930/storageCostsFiller.yml

@manually-enhanced: Do not overwrite. This test measures the regular
gas consumed by storage accesses via `Op.GAS`. EIP-8037 moves the
bulk of storage-write cost into a per-storage state-gas charge; with
an empty state-gas reservoir (these tests pre-allocate none) the full
state gas spills back into regular gas, so each measurement shifts by
its `(Amsterdam - Cancun)` cost delta. Six access classes shift: warm
and cold fresh SSTORE-sets (state-gas spill dominates), warm and cold
SSTORE writes to existing slots (clear/reset: the storage-write
component), cold value-unchanged SSTOREs, and cold SLOADs (the
`COLD_STORAGE_ACCESS` repricing). Warm reads and no-op SSTOREs are
unchanged. Each delta below is derived from the fork's own opcode gas
model, so it is exactly 0 pre-EIP-8037 and tracks future parameter
changes; do not hardcode the Amsterdam numbers.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytes,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Cancun, Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP2930/storageCostsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="declaredKeyWrite",
        ),
        pytest.param(
            1,
            0,
            0,
            id="declaredKeyRead",
        ),
        pytest.param(
            2,
            0,
            0,
            id="declaredKeyDel",
        ),
        pytest.param(
            3,
            0,
            0,
            id="declaredKeyUpdate",
        ),
        pytest.param(
            4,
            0,
            0,
            id="declaredKeyNOP",
        ),
        pytest.param(
            5,
            0,
            0,
            id="declaredKeyNOP0",
        ),
        pytest.param(
            6,
            0,
            0,
            id="undeclaredKeyWrite_otherKey",
        ),
        pytest.param(
            7,
            0,
            0,
            id="undeclaredKeyRead_otherKey",
        ),
        pytest.param(
            8,
            0,
            0,
            id="undeclaredKeyDel_otherKey",
        ),
        pytest.param(
            9,
            0,
            0,
            id="undeclaredKeyUpdate_otherKey",
        ),
        pytest.param(
            10,
            0,
            0,
            id="undeclaredKeyNOP_otherKey",
        ),
        pytest.param(
            11,
            0,
            0,
            id="undeclaredKeyNOP0_otherKey",
        ),
        pytest.param(
            12,
            0,
            0,
            id="undeclaredKeyWrite_otherAddress",
        ),
        pytest.param(
            13,
            0,
            0,
            id="undeclaredKeyRead_otherAddress",
        ),
        pytest.param(
            14,
            0,
            0,
            id="undeclaredKeyDel_otherAddress",
        ),
        pytest.param(
            15,
            0,
            0,
            id="undeclaredKeyUpdate_otherAddress",
        ),
        pytest.param(
            16,
            0,
            0,
            id="undeclaredKeyNOP_otherAddress",
        ),
        pytest.param(
            17,
            0,
            0,
            id="undeclaredKeyNOP0_otherAddress",
        ),
        pytest.param(
            18,
            0,
            0,
            id="undeclaredKeyWrite_noAccessList",
        ),
        pytest.param(
            19,
            0,
            0,
            id="undeclaredKeyRead_noAccessList",
        ),
        pytest.param(
            20,
            0,
            0,
            id="undeclaredKeyDel_noAccessList",
        ),
        pytest.param(
            21,
            0,
            0,
            id="undeclaredKeyUpdate_noAccessList",
        ),
        pytest.param(
            22,
            0,
            0,
            id="undeclaredKeyNOP_noAccessList",
        ),
        pytest.param(
            23,
            0,
            0,
            id="undeclaredKeyNOP0_noAccessList",
        ),
        pytest.param(
            24,
            0,
            0,
            id="declaredKeyWrite_postSSTORE",
        ),
        pytest.param(
            25,
            0,
            0,
            id="undeclaredKeyWrite_postSSTORE",
        ),
        pytest.param(
            26,
            0,
            0,
            id="declaredKeyRead_postSSTORE",
        ),
        pytest.param(
            27,
            0,
            0,
            id="undeclaredKeyRead_postSSTORE",
        ),
        pytest.param(
            28,
            0,
            0,
            id="declaredKeyWrite_postSLOAD",
        ),
        pytest.param(
            29,
            0,
            0,
            id="undeclaredKeyWrite_postSLOAD",
        ),
        pytest.param(
            30,
            0,
            0,
            id="declaredKeyRead_postSLOAD",
        ),
        pytest.param(
            31,
            0,
            0,
            id="undeclaredKeyRead_postSLOAD",
        ),
        pytest.param(
            32,
            0,
            0,
            id="declaredTo",
        ),
        pytest.param(
            33,
            0,
            0,
            id="undeclaredTo_otherAddress",
        ),
        pytest.param(
            34,
            0,
            0,
            id="undeclaredTo_otherKeys",
        ),
        pytest.param(
            35,
            0,
            0,
            id="declaredKeyWrite_manyEntries",
        ),
    ],
)
def test_storage_costs(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0x2)
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    contract_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.SLOAD(key=0x0))
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x13),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    contract_2 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0x0)
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={0: 24743},
        balance=0xDE0B6B3A7640000,
    )
    contract_3 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0xBEEF)
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={0: 24743},
        balance=0xDE0B6B3A7640000,
    )
    contract_4 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0x60A7)
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={0: 24743},
        balance=0xDE0B6B3A7640000,
    )
    contract_5 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0x0)
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={0: 0},
        balance=0xDE0B6B3A7640000,
    )
    contract_6 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x60A7)
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0x2)
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    contract_7 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x60A7)
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.SLOAD(key=0x0))
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x13),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    contract_8 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x20, value=Op.SLOAD(key=0x0))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0x2)
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    contract_9 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x20, value=Op.SLOAD(key=0x0))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.SLOAD(key=0x0))
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x13),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    contract_10 = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x4),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.SLOAD(key=0x60A7))
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x13),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0x2)
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
        )
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={24743: 57005},
        balance=0xBA1A9CE0BA1A9CE,
    )

    # EIP-8037 moves the bulk of storage-write cost into a per-storage
    # state-gas charge. These tests pre-allocate no state-gas reservoir,
    # so the full state gas spills back into regular gas and `Op.GAS`
    # observes each measured SSTORE/SLOAD at its combined regular + state
    # cost. Every measured access therefore shifts by its
    # (Amsterdam - Cancun) delta; derive each delta from the fork's own
    # opcode gas model so it is exactly 0 pre-EIP-8037 and tracks future
    # parameter changes. The subtracted baseline is the same access
    # priced at Cancun.
    def _sstore_delta(**metadata: int) -> int:
        op = Op.SSTORE.with_metadata(**metadata)
        return op.gas_cost(fork) - op.gas_cost(Cancun)

    d_warm_set = _sstore_delta(
        key_warm=True, original_value=0, current_value=0, new_value=2
    )
    d_cold_set = _sstore_delta(
        key_warm=False, original_value=0, current_value=0, new_value=2
    )
    d_warm_write = _sstore_delta(
        key_warm=True, original_value=1, current_value=1, new_value=2
    )
    d_cold_write = _sstore_delta(
        key_warm=False, original_value=1, current_value=1, new_value=2
    )
    d_cold_noop = _sstore_delta(
        key_warm=False, original_value=1, current_value=1, new_value=1
    )
    d_cold_read = (
        fork.gas_costs().COLD_STORAGE_ACCESS
        - Cancun.gas_costs().COLD_STORAGE_ACCESS
    )

    expect_entries_: list[dict] = [
        # declaredKeyWrite: warm fresh SSTORE-set.
        {
            "indexes": {"data": [0, 35], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={0: 2, 1: 20003 + d_warm_set})
            },
        },
        # undeclaredKeyWrite: cold fresh SSTORE-set.
        {
            "indexes": {"data": [6, 12, 18], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={0: 2, 1: 22103 + d_cold_set})
            },
        },
        # declaredKeyUpdate: warm SSTORE-reset (nonzero -> nonzero).
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_3: Account(storage={0: 48879, 1: 2903 + d_warm_write})
            },
        },
        # undeclaredKeyUpdate: cold SSTORE-reset (nonzero -> nonzero).
        {
            "indexes": {"data": [9, 15, 21], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_3: Account(storage={0: 48879, 1: 5003 + d_cold_write})
            },
        },
        # declaredKeyNOP: warm value-unchanged SSTORE (no write).
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_4: Account(storage={0: 24743, 1: 103})},
        },
        # undeclaredKeyNOP: cold value-unchanged SSTORE.
        {
            "indexes": {"data": [10, 16, 22], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_4: Account(storage={0: 24743, 1: 2203 + d_cold_noop})
            },
        },
        # declaredKeyNOP0: warm value-unchanged SSTORE (no write).
        {
            "indexes": {"data": [5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_5: Account(storage={1: 103})},
        },
        # undeclaredKeyNOP0: cold value-unchanged SSTORE.
        {
            "indexes": {"data": [11, 17, 23], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_5: Account(storage={1: 2203 + d_cold_noop})},
        },
        # declaredKeyDel: warm SSTORE-clear (nonzero -> 0).
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_2: Account(storage={0: 0, 1: 2903 + d_warm_write})
            },
        },
        # undeclaredKeyDel: cold SSTORE-clear (nonzero -> 0).
        {
            "indexes": {"data": [8, 14, 20], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_2: Account(storage={0: 0, 1: 5003 + d_cold_write})
            },
        },
        # declaredKeyRead: warm SLOAD.
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_1: Account(storage={1: 100})},
        },
        # undeclaredKeyRead: cold SLOAD.
        {
            "indexes": {"data": [7, 13, 19], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_1: Account(storage={1: 2100 + d_cold_read})},
        },
        # postSSTORE write: key already warm/dirty, no fresh-set spill.
        {
            "indexes": {"data": [24, 25], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_6: Account(storage={0: 2, 1: 103})},
        },
        # postSSTORE read: key already warm.
        {
            "indexes": {"data": [26, 27], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_7: Account(storage={0: 24743, 1: 100})},
        },
        # postSLOAD write: SLOAD warms the key, then warm fresh SSTORE-set.
        {
            "indexes": {"data": [28, 29], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_8: Account(storage={0: 2, 1: 20000 + d_warm_set})
            },
        },
        # postSLOAD read: key already warm.
        {
            "indexes": {"data": [30, 31], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_9: Account(storage={1: 97})},
        },
        # declaredTo: warm SLOAD (slot 1) + warm fresh SSTORE-set (slot 2).
        {
            "indexes": {"data": [32], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_10: Account(
                    storage={
                        0: 2,
                        1: 100,
                        2: 20000 + d_warm_set,
                        24743: 57005,
                    }
                )
            },
        },
        # undeclaredTo: cold SLOAD (slot 1) + cold fresh SSTORE-set (slot 2).
        {
            "indexes": {"data": [33, 34], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_10: Account(
                    storage={
                        0: 2,
                        1: 2100 + d_cold_read,
                        2: 22100 + d_cold_set,
                        24743: 57005,
                    }
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    no_target = pre.nonexistent_account()
    other_address = pre.nonexistent_account()
    tx_data = [
        Bytes("693c6139") + Hash(contract_0, left_padding=True),
        Bytes("693c6139") + Hash(contract_1, left_padding=True),
        Bytes("693c6139") + Hash(contract_2, left_padding=True),
        Bytes("693c6139") + Hash(contract_3, left_padding=True),
        Bytes("693c6139") + Hash(contract_4, left_padding=True),
        Bytes("693c6139") + Hash(contract_5, left_padding=True),
        Bytes("693c6139") + Hash(contract_0, left_padding=True),
        Bytes("693c6139") + Hash(contract_1, left_padding=True),
        Bytes("693c6139") + Hash(contract_2, left_padding=True),
        Bytes("693c6139") + Hash(contract_3, left_padding=True),
        Bytes("693c6139") + Hash(contract_4, left_padding=True),
        Bytes("693c6139") + Hash(contract_5, left_padding=True),
        Bytes("693c6139") + Hash(contract_0, left_padding=True),
        Bytes("693c6139") + Hash(contract_1, left_padding=True),
        Bytes("693c6139") + Hash(contract_2, left_padding=True),
        Bytes("693c6139") + Hash(contract_3, left_padding=True),
        Bytes("693c6139") + Hash(contract_4, left_padding=True),
        Bytes("693c6139") + Hash(contract_5, left_padding=True),
        Bytes("693c6139") + Hash(contract_0, left_padding=True),
        Bytes("693c6139") + Hash(contract_1, left_padding=True),
        Bytes("693c6139") + Hash(contract_2, left_padding=True),
        Bytes("693c6139") + Hash(contract_3, left_padding=True),
        Bytes("693c6139") + Hash(contract_4, left_padding=True),
        Bytes("693c6139") + Hash(contract_5, left_padding=True),
        Bytes("693c6139") + Hash(contract_6, left_padding=True),
        Bytes("693c6139") + Hash(contract_6, left_padding=True),
        Bytes("693c6139") + Hash(contract_7, left_padding=True),
        Bytes("693c6139") + Hash(contract_7, left_padding=True),
        Bytes("693c6139") + Hash(contract_8, left_padding=True),
        Bytes("693c6139") + Hash(contract_8, left_padding=True),
        Bytes("693c6139") + Hash(contract_9, left_padding=True),
        Bytes("693c6139") + Hash(contract_9, left_padding=True),
        Bytes("693c6139") + Hash(no_target, left_padding=True),
        Bytes("693c6139") + Hash(no_target, left_padding=True),
        Bytes("693c6139") + Hash(no_target, left_padding=True),
        Bytes("693c6139") + Hash(contract_0, left_padding=True),
    ]
    tx_value = [100000]
    tx_access_lists: dict[int, list] = {
        0: [
            AccessList(
                address=contract_0,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        1: [
            AccessList(
                address=contract_1,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        2: [
            AccessList(
                address=contract_2,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        3: [
            AccessList(
                address=contract_3,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        4: [
            AccessList(
                address=contract_4,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        5: [
            AccessList(
                address=contract_5,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        6: [
            AccessList(
                address=contract_0,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        7: [
            AccessList(
                address=contract_1,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        8: [
            AccessList(
                address=contract_2,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        9: [
            AccessList(
                address=contract_3,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        10: [
            AccessList(
                address=contract_4,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        11: [
            AccessList(
                address=contract_5,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        12: [
            AccessList(
                address=other_address,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        13: [
            AccessList(
                address=other_address,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        14: [
            AccessList(
                address=other_address,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        15: [
            AccessList(
                address=other_address,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        16: [
            AccessList(
                address=other_address,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        17: [
            AccessList(
                address=other_address,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        24: [
            AccessList(
                address=contract_6,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        25: [
            AccessList(
                address=contract_6,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        26: [
            AccessList(
                address=contract_7,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        27: [
            AccessList(
                address=contract_7,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        28: [
            AccessList(
                address=contract_8,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        29: [
            AccessList(
                address=contract_8,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        30: [
            AccessList(
                address=contract_9,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        31: [
            AccessList(
                address=contract_9,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        32: [
            AccessList(
                address=contract_10,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000002"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        33: [
            AccessList(
                address=other_address,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000002"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        34: [
            AccessList(
                address=contract_10,
                storage_keys=[
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f001"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f002"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f0a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        35: [
            AccessList(
                address=Address(0x00000000000000000000000000000000000060A7),
                storage_keys=[
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000fffffad"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000000ad"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000123214342ad"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000deadbeef"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
            AccessList(
                address=contract_0,
                storage_keys=[
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000fffff"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000123214342"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000deadbeef"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
            AccessList(
                address=Address(0x0000000000000000000000000010000000000100),
                storage_keys=[
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000fffffbc"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000000bc"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000123214342bc"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000deadbeefbc"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
            AccessList(
                address=Address(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
                storage_keys=[
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000fffffbc"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000000bc"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000123214342bc"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000deadbeefbc"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0xdeadbeef12345678deadbeef12345678deadbeef12345678deadbeef12345678"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
    }

    tx = Transaction(
        sender=sender,
        to=contract_10,
        data=tx_data[d],
        value=tx_value[v],
        access_list=tx_access_lists.get(d),
        state_gas_reservoir=0,
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
