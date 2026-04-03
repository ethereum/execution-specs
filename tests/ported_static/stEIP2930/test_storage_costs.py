"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP2930/storageCostsFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    AccessList,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

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
            id="undeclaredKeyWrite",
        ),
        pytest.param(
            7,
            0,
            0,
            id="undeclaredKeyRead",
        ),
        pytest.param(
            8,
            0,
            0,
            id="undeclaredKeyDel",
        ),
        pytest.param(
            9,
            0,
            0,
            id="undeclaredKeyUpdate",
        ),
        pytest.param(
            10,
            0,
            0,
            id="undeclaredKeyNOP",
        ),
        pytest.param(
            11,
            0,
            0,
            id="undeclaredKeyNOP0",
        ),
        pytest.param(
            12,
            0,
            0,
            id="undeclaredKeyWrite",
        ),
        pytest.param(
            13,
            0,
            0,
            id="undeclaredKeyRead",
        ),
        pytest.param(
            14,
            0,
            0,
            id="undeclaredKeyDel",
        ),
        pytest.param(
            15,
            0,
            0,
            id="undeclaredKeyUpdate",
        ),
        pytest.param(
            16,
            0,
            0,
            id="undeclaredKeyNOP",
        ),
        pytest.param(
            17,
            0,
            0,
            id="undeclaredKeyNOP0",
        ),
        pytest.param(
            18,
            0,
            0,
            id="undeclaredKeyWrite",
        ),
        pytest.param(
            19,
            0,
            0,
            id="undeclaredKeyRead",
        ),
        pytest.param(
            20,
            0,
            0,
            id="undeclaredKeyDel",
        ),
        pytest.param(
            21,
            0,
            0,
            id="undeclaredKeyUpdate",
        ),
        pytest.param(
            22,
            0,
            0,
            id="undeclaredKeyNOP",
        ),
        pytest.param(
            23,
            0,
            0,
            id="undeclaredKeyNOP0",
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
            id="undeclaredTo",
        ),
        pytest.param(
            34,
            0,
            0,
            id="undeclaredTo",
        ),
        pytest.param(
            35,
            0,
            0,
            id="declaredKeyWrite",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_storage_costs(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x0000000000000000000000000000000000001000)
    contract_1 = Address(0x0000000000000000000000000000000000001001)
    contract_2 = Address(0x0000000000000000000000000000000000001002)
    contract_3 = Address(0x0000000000000000000000000000000000001003)
    contract_4 = Address(0x0000000000000000000000000000000000001004)
    contract_5 = Address(0x0000000000000000000000000000000000001005)
    contract_6 = Address(0x0000000000000000000000000000000000001010)
    contract_7 = Address(0x0000000000000000000000000000000000001011)
    contract_8 = Address(0x0000000000000000000000000000000000001020)
    contract_9 = Address(0x0000000000000000000000000000000000001021)
    contract_10 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    # Source: lll
    # {
    #  ; Write to @@0, and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #   [[0]]  0x02
    #    [0]   (- @0 (gas) 17)
    #   [[1]] @0
    #
    #  ; The 17 is the cost of the extra opcodes:
    #  ; PUSH1 0x00, MSTORE
    #  ; PUSH1 0x02, PUSH1 0x00, (and then comes the SSTORE we are measuring)
    #  ; GAS
    #
    #  ; If the storage cell is declared the cost in @@1 should be 20003
    #  ; If the storage cell is not declared the cost    should be 22103
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0x2)
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001000),  # noqa: E501
    )
    # Source: lll
    # {
    #  ; Read @@0, and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #    @@0
    #    [0]   (- @0 (gas) 19)
    #   [[1]] @0
    #
    #  ; If the storage cell is declared the cost in @@1 should be  100
    #  ; If the storage cell is not declared the cost    should be 2100
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.SLOAD(key=0x0))
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x13),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001001),  # noqa: E501
    )
    # Source: lll
    # {
    #  ; Write to @@0, and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #   [[0]]  0x00
    #    [0]   (- @0 (gas) 17)
    #   [[1]] @0
    #
    #  ; The 17 is the cost of the extra opcodes:
    #  ; PUSH1 0x00, MSTORE
    #  ; PUSH1 0x02, PUSH1 0x00, (and then comes the SSTORE we are measuring)
    #  ; GAS
    #
    #  ; If the storage cell is declared the cost in @@1 should be 2903
    #  ; If the storage cell is not declared the cost    should be 5003
    #  ;
    #  ; The refund for freeing memory happens at the end of the transaction,
    #  ; so we don't see it
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
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
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001002),  # noqa: E501
    )
    # Source: lll
    # {
    #  ; Write to @@0, and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #   [[0]]  0xBEEF
    #    [0]   (- @0 (gas) 17)
    #   [[1]] @0
    #
    #  ; The 17 is the cost of the extra opcodes:
    #  ; PUSH1 0x00, MSTORE
    #  ; PUSH1 0x02, PUSH1 0x00, (and then comes the SSTORE we are measuring)
    #  ; GAS
    #
    #  ; If the storage cell is declared the cost in @@1 should be  103
    #  ; If the storage cell is not declared the cost    should be 2203
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
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
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001003),  # noqa: E501
    )
    # Source: lll
    # {
    #  ; Write to @@0, and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #   [[0]]  0x60A7
    #    [0]   (- @0 (gas) 17)
    #   [[1]] @0
    #
    #  ; The 17 is the cost of the extra opcodes:
    #  ; PUSH1 0x00, MSTORE
    #  ; PUSH1 0x02, PUSH1 0x00, (and then comes the SSTORE we are measuring)
    #  ; GAS
    #
    #  ; This costs 103, regadless of whether it is declared or not
    # }
    contract_4 = pre.deploy_contract(  # noqa: F841
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
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001004),  # noqa: E501
    )
    # Source: lll
    # {
    #  ; Write to @@0, and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #   [[0]]  0x00
    #    [0]   (- @0 (gas) 17)
    #   [[1]] @0
    #
    #  ; The 17 is the cost of the extra opcodes:
    #  ; PUSH1 0x00, MSTORE
    #  ; PUSH1 0x02, PUSH1 0x00, (and then comes the SSTORE we are measuring)
    #  ; GAS
    #
    #  ; This costs 103, regadless of whether it is declared or not
    # }
    contract_5 = pre.deploy_contract(  # noqa: F841
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
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001005),  # noqa: E501
    )
    # Source: lll
    # {
    #
    #   [[0]] 0x60A7
    #
    #  ; Write to @@0, and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #   [[0]]  0x02
    #    [0]   (- @0 (gas) 17)
    #   [[1]] @0
    #
    #  ; The 17 is the cost of the extra opcodes:
    #  ; PUSH1 0x00, MSTORE
    #  ; PUSH1 0x02, PUSH1 0x00, (and then comes the SSTORE we are measuring)
    #  ; GAS
    #
    #  ; Since this is second access, it will cost 103
    #  ; regardless of whether it was declared or not
    #
    # }
    contract_6 = pre.deploy_contract(  # noqa: F841
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
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001010),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[0]] 0x60A7
    #
    #  ; Read @@0, and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #    @@0
    #    [0]   (- @0 (gas) 19)
    #   [[1]] @0
    #
    #  ; Since this is second access, it will cost 100
    #  ; regardless of whether it was declared or not
    # }
    contract_7 = pre.deploy_contract(  # noqa: F841
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
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001011),  # noqa: E501
    )
    # Source: lll
    # {
    #   [0x20] @@0
    #
    #  ; Write to @@0, and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #   [[0]]  0x02
    #    [0]   (- @0 (gas) 17)
    #   [[1]] @0
    #
    #  ; The 17 is the cost of the extra opcodes:
    #  ; PUSH1 0x00, MSTORE
    #  ; PUSH1 0x02, PUSH1 0x00, (and then comes the SSTORE we are measuring)
    #  ; GAS
    #
    #  ; Since this is second access, it will cost 20k
    #  ; regardless of whether it was declared or not
    #
    # }
    contract_8 = pre.deploy_contract(  # noqa: F841
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
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001020),  # noqa: E501
    )
    # Source: lll
    # {
    #   [0x20] @@0
    #
    #  ; Read @@0, and see how much gas that cost.
    #    [0]   (gas)
    #    @@0
    #    [0]   (- @0 (gas) 19)
    #   [[1]] @0
    #
    #  ; Since this is second access, it will cost 97
    #  ; regardless of whether it was declared or not
    # }
    contract_9 = pre.deploy_contract(  # noqa: F841
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
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001021),  # noqa: E501
    )
    # Source: lll
    # { ; TO_ADDR_VALID   TO_ADDR_INVALID_ADDR    TO_ADDR_INVALID_CELL
    #   ; Call a different contract
    #   (call (gas) (+ 0x1000 $4) 0 0 0 0 0)
    #
    #   ; Read @@0, and see how much gas that cost.
    #     [0]   (gas)
    #     @@0x60A7
    #     [0]   (- @0 (gas) 19)
    #    [[1]] @0
    #
    #
    #   ; Write to @@0, and see how much gas that cost. It should
    #   ; cost more when it is not declared storage
    #     [0]   (gas)
    #    [[0]]  0x02
    #     [0]   (- @0 (gas) 17)
    #    [[2]] @0
    #
    #   ; The 17 is the cost of the extra opcodes:
    #   ; PUSH1 0x00, MSTORE
    #   ; PUSH1 0x02, PUSH1 0x00, (and then comes the SSTORE we are measuring)
    #   ; GAS
    #
    #
    # }
    contract_10 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
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
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 35], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 2, 1: 20003})},
        },
        {
            "indexes": {"data": [6, 12, 18], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 2, 1: 22103})},
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_3: Account(storage={0: 48879, 1: 2903})},
        },
        {
            "indexes": {"data": [9, 15, 21], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_3: Account(storage={0: 48879, 1: 5003})},
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_4: Account(storage={0: 24743, 1: 103})},
        },
        {
            "indexes": {"data": [10, 16, 22], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_4: Account(storage={0: 24743, 1: 2203})},
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_5: Account(storage={1: 103})},
        },
        {
            "indexes": {"data": [11, 17, 23], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_5: Account(storage={1: 2203})},
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_2: Account(storage={0: 0, 1: 2903})},
        },
        {
            "indexes": {"data": [8, 14, 20], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_2: Account(storage={0: 0, 1: 5003})},
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_1: Account(storage={1: 100})},
        },
        {
            "indexes": {"data": [7, 13, 19], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_1: Account(storage={1: 2100})},
        },
        {
            "indexes": {"data": [24, 25], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_6: Account(storage={0: 2, 1: 103})},
        },
        {
            "indexes": {"data": [26, 27], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_7: Account(storage={0: 24743, 1: 100})},
        },
        {
            "indexes": {"data": [28, 29], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_8: Account(storage={0: 2, 1: 20000})},
        },
        {
            "indexes": {"data": [30, 31], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_9: Account(storage={1: 97})},
        },
        {
            "indexes": {"data": [32], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_10: Account(
                    storage={0: 2, 1: 100, 2: 20000, 24743: 57005}
                )
            },
        },
        {
            "indexes": {"data": [33, 34], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_10: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005}
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x1),
        Bytes("693c6139") + Hash(0x2),
        Bytes("693c6139") + Hash(0x3),
        Bytes("693c6139") + Hash(0x4),
        Bytes("693c6139") + Hash(0x5),
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x1),
        Bytes("693c6139") + Hash(0x2),
        Bytes("693c6139") + Hash(0x3),
        Bytes("693c6139") + Hash(0x4),
        Bytes("693c6139") + Hash(0x5),
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x1),
        Bytes("693c6139") + Hash(0x2),
        Bytes("693c6139") + Hash(0x3),
        Bytes("693c6139") + Hash(0x4),
        Bytes("693c6139") + Hash(0x5),
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x1),
        Bytes("693c6139") + Hash(0x2),
        Bytes("693c6139") + Hash(0x3),
        Bytes("693c6139") + Hash(0x4),
        Bytes("693c6139") + Hash(0x5),
        Bytes("693c6139") + Hash(0x10),
        Bytes("693c6139") + Hash(0x10),
        Bytes("693c6139") + Hash(0x11),
        Bytes("693c6139") + Hash(0x11),
        Bytes("693c6139") + Hash(0x20),
        Bytes("693c6139") + Hash(0x20),
        Bytes("693c6139") + Hash(0x21),
        Bytes("693c6139") + Hash(0x21),
        Bytes("693c6139") + Hash(0xFFF),
        Bytes("693c6139") + Hash(0xFFF),
        Bytes("693c6139") + Hash(0xFFF),
        Bytes("693c6139") + Hash(0x0),
    ]
    tx_gas = [400000]
    tx_value = [100000]
    tx_access_lists: dict[int, list] = {
        0: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001000),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        1: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001001),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        2: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001002),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        3: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001003),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        4: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001004),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        5: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001005),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        6: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001000),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        7: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001001),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        8: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001002),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        9: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001003),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        10: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001004),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        11: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001005),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        12: [
            AccessList(
                address=Address(0xF000000000000000000000000000000000000100),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        13: [
            AccessList(
                address=Address(0xF000000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        14: [
            AccessList(
                address=Address(0xF000000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        15: [
            AccessList(
                address=Address(0xF000000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        16: [
            AccessList(
                address=Address(0xF000000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        17: [
            AccessList(
                address=Address(0xF000000000000000000000000000000000000101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        24: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001010),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        25: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001010),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        26: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001011),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        27: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001011),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        28: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001020),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        29: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001020),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        30: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001021),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        31: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001021),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        32: [
            AccessList(
                address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),
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
                address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000),
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
                address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),
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
                address=Address(0x0000000000000000000000000000000000001000),
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
        gas_limit=tx_gas[g],
        value=tx_value[v],
        access_list=tx_access_lists.get(d),
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
