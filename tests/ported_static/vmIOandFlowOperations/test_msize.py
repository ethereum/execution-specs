"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/msizeFiller.yml
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
    ["state_tests/VMTests/vmIOandFlowOperations/msizeFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="msize0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="msize1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="msize2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="msize3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="chunks",
        ),
        pytest.param(
            5,
            0,
            0,
            id="farChunk",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_msize(
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
    contract_6 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4294967296,
    )

    # Source: lll
    # {
    #     ; Store an entire 32 byte value
    #     [0]  0xFF
    #    [[0]] (msize)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0xFF)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001000),  # noqa: E501
    )
    # Source: lll
    # {
    #     ; Store an entire 32 byte value
    #     [0]  0xffffffffff
    #    [[0]] (msize)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0xFFFFFFFFFF)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001001),  # noqa: E501
    )
    # Source: lll
    # {
    #     ; Store two values
    #    [0]    0xffffffffff
    #    [0x20] 0xeeee
    #    [[0]] (msize)
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0xFFFFFFFFFF)
        + Op.MSTORE(offset=0x20, value=0xEEEE)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001002),  # noqa: E501
    )
    # Source: lll
    # {
    #     ; Store two values
    #    [0]    0xffffffffff
    #    [0x5a] 0xeeee
    #    [[0]] (msize)
    #
    #    ; The 0xEEEE value is stored 0x5a-0x79,
    #    ; and memory is allocated in 0x20 byte chunks
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0xFFFFFFFFFF)
        + Op.MSTORE(offset=0x5A, value=0xEEEE)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001003),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; Store at the very end of the first chunk
    #    (mstore8 0x1F 1)
    #    [[0]] (msize)
    #
    #    ; Store at the beginning of the second chuck
    #    (mstore8 0x20 1)
    #    [[1]] (msize)
    #
    #    ; Does it matter if we reset the memory?
    #    ; Spoiler alert, it doesn't
    #    (mstore8 0x20 0)
    #    [[2]] (msize)
    #
    # }
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x1F, value=0x1)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.MSTORE8(offset=0x20, value=0x1)
        + Op.SSTORE(key=0x1, value=Op.MSIZE)
        + Op.MSTORE8(offset=0x20, value=0x0)
        + Op.SSTORE(key=0x2, value=Op.MSIZE)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001004),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; Does the chunk size change in very high offsets?
    #    ;
    #    ; Note: It doesn't
    #    (mstore8 0xB00000 1)
    #    [[0]] (msize)
    # }
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0xB00000, value=0x1)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001005),  # noqa: E501
    )
    # Source: lll
    # {
    #     (delegatecall (gas) (+ 0x1000 $4) 0 0 0 0)
    # }
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=Op.GAS,
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
    pre[sender] = Account(balance=0x100000000000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 1], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract_6: Account(storage={0: 32})},
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract_6: Account(storage={0: 64})},
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract_6: Account(storage={0: 128})},
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract_6: Account(storage={0: 32, 1: 64, 2: 64})},
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract_6: Account(storage={0: 0xB00020})},
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
    ]
    tx_gas = [268435456]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_6,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
