"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
state_tests/stCreateTest/createLargeResultFiller.yml
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
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/createLargeResultFiller.yml"],
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
            id="CREATE-RETURN",
        ),
        pytest.param(
            1,
            0,
            0,
            id="CREATE2-RETURN",
        ),
        pytest.param(
            2,
            0,
            0,
            id="CREATE-REVERT",
        ),
        pytest.param(
            3,
            0,
            0,
            id="CREATE2-REVERT",
        ),
        pytest.param(
            4,
            0,
            0,
            id="CREATE-RETURN-MAX",
        ),
        pytest.param(
            5,
            0,
            0,
            id="CREATE2-RETURN-MAX",
        ),
        pytest.param(
            6,
            0,
            0,
            id="CREATE-REVERT-MAX",
        ),
        pytest.param(
            7,
            0,
            0,
            id="CREATE2-REVERT-MAX",
        ),
        pytest.param(
            8,
            0,
            0,
            id="CREATE-RETURN-TOOBIG",
        ),
        pytest.param(
            9,
            0,
            0,
            id="CREATE2-RETURN-TOOBIG",
        ),
        pytest.param(
            10,
            0,
            0,
            id="CREATE-REVERT-TOOBIG",
        ),
        pytest.param(
            11,
            0,
            0,
            id="CREATE2-REVERT-TOOBIG",
        ),
        pytest.param(
            12,
            0,
            0,
            id="CREATE-RETURN-HUGE",
        ),
        pytest.param(
            13,
            0,
            0,
            id="CREATE2-RETURN-HUGE",
        ),
        pytest.param(
            14,
            0,
            0,
            id="CREATE-REVERT-HUGE",
        ),
        pytest.param(
            15,
            0,
            0,
            id="CREATE2-REVERT-HUGE",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_large_result(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x000000000000000000000000000000000000C0DE)
    contract_1 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
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

    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
    # Source: yul
    # london
    # {
    #    // Store some data
    #    mstore(0, not(0))
    #
    #    // Copy the requested length from the constructor code
    #    codecopy(0x100, 0x100, 0x20)
    #
    #    // Return it as the new contract
    #    return(0, mload(0x100))
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.NOT(0x0))
        + Op.CODECOPY(dest_offset=Op.DUP1, offset=0x100, size=0x20)
        + Op.RETURN(offset=0x0, size=Op.MLOAD(offset=0x100)),
        nonce=1,
        address=Address(0x000000000000000000000000000000000000C0DE),  # noqa: E501
    )
    # Source: yul
    # london
    # {
    #   sstore(1, gas())
    #
    #   // The operation to run
    #   // F0 - CREATE
    #   // F5 - CREATE2
    #   let operation := calldataload(0x04)
    #
    #   // The constructor ends with
    #   // F3 - RETURN
    #   // FD - REVERT
    #   let constructorEnd := calldataload(0x24)
    #
    #   // The size of the contract getting created
    #   let contractSize := calldataload(0x44)
    #
    #   // Create the constructor.
    #   let codeSize := extcodesize(0xC0DE)
    #   extcodecopy(0xC0DE, 0, 0, codeSize)
    #
    #   // Modify the last opcode
    #   mstore8(sub(codeSize, 1), constructorEnd)
    #
    #   // Include the requested contract size
    #   mstore(0x100, contractSize)
    #
    #   // Create the contract
    #   let newAddr
    #   switch operation
    # ... (10 more lines)
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=Op.GAS)
        + Op.CALLDATALOAD(offset=0x4)
        + Op.CALLDATALOAD(offset=0x24)
        + Op.CALLDATALOAD(offset=0x44)
        + Op.SWAP1
        + Op.PUSH1[0x1]
        + Op.EXTCODESIZE(address=contract_0)
        + Op.EXTCODECOPY(
            address=contract_0, dest_offset=Op.DUP1, offset=0x0, size=Op.DUP1
        )
        + Op.SUB
        + Op.MSTORE8
        + Op.PUSH2[0x100]
        + Op.MSTORE
        + Op.PUSH1[0x0]
        + Op.SWAP1
        + Op.JUMPI(pc=0x53, condition=Op.EQ(0xF0, Op.DUP1))
        + Op.PUSH1[0xF5]
        + Op.JUMPI(pc=0x44, condition=Op.EQ)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=Op.DUP1)
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.SLOAD(key=0x1), Op.GAS))
        + Op.SSTORE(key=0x2, value=Op.EXTCODEHASH)
        + Op.STOP
        + Op.JUMPDEST
        + Op.POP
        + Op.CREATE2(value=Op.DUP1, offset=0x0, size=0x120, salt=0x5A17)
        + Op.JUMP(pc=0x32)
        + Op.JUMPDEST
        + Op.POP * 2
        + Op.CREATE(value=Op.DUP1, offset=0x0, size=0x120)
        + Op.JUMP(pc=0x32),
        storage={0: 24743, 1: 24743, 2: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_1: Account(
                    storage={
                        0: compute_create_address(address=contract_1, nonce=1),
                        1: 0x1777F,
                        2: 0xD956C0ABD597440481902014A37B733358EE7685461EB1B5916EEFD83381E6D9,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_1: Account(
                    storage={
                        0: 0x595C5D0C272757CFF0B3DCA4ED60D60CD6E9F58,
                        1: 0x177C9,
                        2: 0xD956C0ABD597440481902014A37B733358EE7685461EB1B5916EEFD83381E6D9,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract_1: Account(storage={0: 0, 1: 44927, 2: 0})},
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract_1: Account(storage={0: 0, 1: 45001, 2: 0})},
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_1: Account(
                    storage={
                        0: compute_create_address(address=contract_1, nonce=1),
                        1: 0x4BBCE4,
                        2: 0xDCBCC213F0C91B71D38DEDD06C95CCB99467B9B05F275BED536DE1044F5F18FA,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_1: Account(
                    storage={
                        0: 0xA5DC71D47D0D8DCF5990E81C74E981BAF24A8FA2,
                        1: 0x4BBD2E,
                        2: 0xDCBCC213F0C91B71D38DEDD06C95CCB99467B9B05F275BED536DE1044F5F18FA,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [6], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract_1: Account(storage={0: 0, 1: 48356, 2: 0})},
        },
        {
            "indexes": {"data": [7], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract_1: Account(storage={0: 0, 1: 48430, 2: 0})},
        },
        {
            "indexes": {"data": [8], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_1: Account(storage={0: 0, 1: 0x4B16491, 2: 0})
            },
        },
        {
            "indexes": {"data": [9], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_1: Account(storage={0: 0, 1: 0x4B16492, 2: 0})
            },
        },
        {
            "indexes": {"data": [10], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract_1: Account(storage={0: 0, 1: 48362, 2: 0})},
        },
        {
            "indexes": {"data": [11], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract_1: Account(storage={0: 0, 1: 48436, 2: 0})},
        },
        {
            "indexes": {"data": [12], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_1: Account(storage={0: 0, 1: 0x4B1649D, 2: 0})
            },
        },
        {
            "indexes": {"data": [13], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_1: Account(storage={0: 0, 1: 0x4B1649E, 2: 0})
            },
        },
        {
            "indexes": {"data": [14], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract_1: Account(storage={0: 0, 1: 54116, 2: 0})},
        },
        {
            "indexes": {"data": [15], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract_1: Account(storage={0: 0, 1: 54190, 2: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("048071d3") + Hash(0xF0) + Hash(0xF3) + Hash(0x100),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xF3) + Hash(0x100),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xFD) + Hash(0x100),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xFD) + Hash(0x100),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xF3) + Hash(0x6000),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xF3) + Hash(0x6000),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xFD) + Hash(0x6000),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xFD) + Hash(0x6000),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xF3) + Hash(0x6001),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xF3) + Hash(0x6001),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xFD) + Hash(0x6001),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xFD) + Hash(0x6001),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xF3) + Hash(0xC000),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xF3) + Hash(0xC000),
        Bytes("048071d3") + Hash(0xF0) + Hash(0xFD) + Hash(0xC000),
        Bytes("048071d3") + Hash(0xF5) + Hash(0xFD) + Hash(0xC000),
    ]
    tx_gas = [80000000]

    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
