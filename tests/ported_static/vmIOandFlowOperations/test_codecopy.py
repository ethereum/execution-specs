"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/codecopyFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
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
    ["state_tests/VMTests/vmIOandFlowOperations/codecopyFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="codecopy",
        ),
        pytest.param(
            1,
            0,
            0,
            id="codecopy_infbuff",
        ),
        pytest.param(
            2,
            0,
            0,
            id="codecopy_bigbuff",
        ),
        pytest.param(
            3,
            0,
            0,
            id="codecopy_2buff",
        ),
        pytest.param(
            4,
            0,
            0,
            id="codecopy_opcodes",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_codecopy(
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
    contract_5 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # {
    #    ; Copy our code into [[0]] and [[1]]
    #    (codecopy 0 0 0x40)
    #    [[0]] @0
    #    [[1]] @0x20
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.CODECOPY(dest_offset=0x0, offset=0x0, size=0x40)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001000),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; Copy our code into [[0]] and [[1]]
    #    (codecopy 0 0 (- 0 1))
    #    [[0]] @0
    #    [[1]] @0x20
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.CODECOPY(dest_offset=0x0, offset=0x0, size=Op.SUB(0x0, 0x1))
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001001),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; Copy our code into [[0]] and [[1]]
    #    (codecopy 0 0 0x1000)
    #    [[0]] @0
    #    [[1]] @0x20
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.CODECOPY(dest_offset=0x0, offset=0x0, size=0x1000)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001002),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; Waste some space so we'll be over 0x20 bytes of code
    #    [0x100] (+ 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)
    #
    #    ; Copy our code into [[0]] and [[1]]
    #    (codecopy    0    0 0x20)
    #    (codecopy 0x20 0x20 0x40)
    #    [[0]] @0
    #    [[1]] @0x20
    #    [[2]] @0x40
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x100,
            value=Op.ADD(
                Op.ADD(
                    Op.ADD(
                        Op.ADD(
                            Op.ADD(
                                Op.ADD(
                                    Op.ADD(
                                        Op.ADD(
                                            Op.ADD(
                                                Op.ADD(
                                                    Op.ADD(
                                                        Op.ADD(
                                                            Op.ADD(
                                                                Op.ADD(
                                                                    Op.ADD(
                                                                        0x1,
                                                                        0x2,
                                                                    ),
                                                                    0x3,
                                                                ),
                                                                0x4,
                                                            ),
                                                            0x5,
                                                        ),
                                                        0x6,
                                                    ),
                                                    0x7,
                                                ),
                                                0x8,
                                            ),
                                            0x9,
                                        ),
                                        0xA,
                                    ),
                                    0xB,
                                ),
                                0xC,
                            ),
                            0xD,
                        ),
                        0xE,
                    ),
                    0xF,
                ),
                0x10,
            ),
        )
        + Op.CODECOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.CODECOPY(dest_offset=0x20, offset=0x20, size=0x40)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x40))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001003),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; Get our size
    #    [[0xFF]] (codesize)
    #
    #    ; Copy our code to memory
    #    (codecopy 0 0 @@0xFF)
    #
    #    ; Make it clear the storage we use gets overwritten
    #    [[0]] 0x60A7
    #    [[1]] 0x60A7
    #    [[2]] 0x60A7
    #
    #    ; Copy the memory into storage
    #    [[0]] @0x00
    #    [[1]] @0x20
    #    [[2]] @0x40
    #    [[3]] @0x60
    #    [[4]] @0x80
    #    [[5]] @0xA0
    #
    #    ; Potentially problematic opcodes
    #    (stop)
    #    (selfdestruct 0xDEAD)
    #    (return 0x0 @@0xFF)
    #    (delegatecall 0xFF 0xEE 0xDD 0xCC 0xBB 0xAA)
    # }
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0xFF, value=Op.CODESIZE)
        + Op.CODECOPY(dest_offset=0x0, offset=0x0, size=Op.SLOAD(key=0xFF))
        + Op.SSTORE(key=0x0, value=0x60A7)
        + Op.SSTORE(key=0x1, value=0x60A7)
        + Op.SSTORE(key=0x2, value=0x60A7)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x40))
        + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x60))
        + Op.SSTORE(key=0x4, value=Op.MLOAD(offset=0x80))
        + Op.SSTORE(key=0x5, value=Op.MLOAD(offset=0xA0))
        + Op.STOP
        + Op.SELFDESTRUCT(address=0xDEAD)
        + Op.RETURN(offset=0x0, size=Op.SLOAD(key=0xFF))
        + Op.DELEGATECALL(
            gas=0xFF,
            address=0xEE,
            args_offset=0xDD,
            args_size=0xCC,
            ret_offset=0xBB,
            ret_size=0xAA,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001004),  # noqa: E501
    )
    # Source: lll
    # {
    #     (delegatecall 0xffffff (+ 0x1000 $4) 0 0 0 0)
    # }
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=0xFFFFFF,
            address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_5: Account(
                    storage={
                        0: 0x6040600060003960005160005560205160015500000000000000000000000000,  # noqa: E501
                        1: 0,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_5: Account(
                    storage={
                        0: 0x6110006000600039600051600055602051600155000000000000000000000000,  # noqa: E501
                        1: 0,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_5: Account(storage={0: 0, 1: 0})},
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_5: Account(
                    storage={
                        0: 0x6010600F600E600D600C600B600A600960086007600660056004600360026001,  # noqa: E501
                        1: 0x101010101010101010101010101016101005260206000600039604060206020,  # noqa: E501
                        2: 0x3960005160005560205160015560405160025500000000000000000000000000,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_5: Account(
                    storage={
                        0: 0x3860FF5560FF5460006000396160A76000556160A76001556160A76002556000,  # noqa: E501
                        1: 0x5160005560205160015560405160025560605160035560805160045560A05160,  # noqa: E501
                        2: 0x5550061DEADFF60FF546000F360AA60BB60CC60DD60EE60FFF4000000000000,  # noqa: E501
                        255: 91,
                    },
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
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_5,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
