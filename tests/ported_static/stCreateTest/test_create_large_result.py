"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stCreateTest/createLargeResultFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
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

TX_DATA = [
    "048071d300000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f30000000000000000000000000000000000000000000000000000000000000100",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f500000000000000000000000000000000000000000000000000000000000000f30000000000000000000000000000000000000000000000000000000000000100",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000fd0000000000000000000000000000000000000000000000000000000000000100",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f500000000000000000000000000000000000000000000000000000000000000fd0000000000000000000000000000000000000000000000000000000000000100",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f30000000000000000000000000000000000000000000000000000000000006000",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f500000000000000000000000000000000000000000000000000000000000000f30000000000000000000000000000000000000000000000000000000000006000",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000fd0000000000000000000000000000000000000000000000000000000000006000",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f500000000000000000000000000000000000000000000000000000000000000fd0000000000000000000000000000000000000000000000000000000000006000",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f30000000000000000000000000000000000000000000000000000000000006001",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f500000000000000000000000000000000000000000000000000000000000000f30000000000000000000000000000000000000000000000000000000000006001",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000fd0000000000000000000000000000000000000000000000000000000000006001",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f500000000000000000000000000000000000000000000000000000000000000fd0000000000000000000000000000000000000000000000000000000000006001",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f3000000000000000000000000000000000000000000000000000000000000c000",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f500000000000000000000000000000000000000000000000000000000000000f3000000000000000000000000000000000000000000000000000000000000c000",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000fd000000000000000000000000000000000000000000000000000000000000c000",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f500000000000000000000000000000000000000000000000000000000000000fd000000000000000000000000000000000000000000000000000000000000c000",  # noqa: E501
]

TX_GAS = [80000000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stCreateTest/createLargeResultFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(12, 0, 0, id="case0"),
        pytest.param(4, 0, 0, id="case1"),
        pytest.param(8, 0, 0, id="case2"),
        pytest.param(0, 0, 0, id="case3"),
        pytest.param(14, 0, 0, id="case4"),
        pytest.param(6, 0, 0, id="case5"),
        pytest.param(10, 0, 0, id="case6"),
        pytest.param(2, 0, 0, id="case7"),
        pytest.param(13, 0, 0, id="case8"),
        pytest.param(5, 0, 0, id="case9"),
        pytest.param(9, 0, 0, id="case10"),
        pytest.param(1, 0, 0, id="case11"),
        pytest.param(15, 0, 0, id="case12"),
        pytest.param(7, 0, 0, id="case13"),
        pytest.param(11, 0, 0, id="case14"),
        pytest.param(3, 0, 0, id="case15"),
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
    """Ori Pomerantz   qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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

    # Source: Yul
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
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.NOT(0x0))
            + Op.CODECOPY(dest_offset=Op.DUP1, offset=0x100, size=0x20)
            + Op.RETURN(offset=0x0, size=Op.MLOAD(offset=0x100))
        ),
        address=Address("0x000000000000000000000000000000000000c0de"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
    # Source: Yul
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
    #   case 0xF0 { newAddr := create(0, 0, 0x120) }
    # ... (9 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=Op.GAS)
            + Op.CALLDATALOAD(offset=0x4)
            + Op.CALLDATALOAD(offset=0x24)
            + Op.CALLDATALOAD(offset=0x44)
            + Op.SWAP1
            + Op.PUSH1[0x1]
            + Op.EXTCODESIZE(address=0xC0DE)
            + Op.EXTCODECOPY(
                address=0xC0DE,
                dest_offset=Op.DUP1,
                offset=0x0,
                size=Op.DUP1,
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
            + Op.POP
            + Op.POP
            + Op.CREATE(value=Op.DUP1, offset=0x0, size=0x120)
            + Op.JUMP(pc=0x32)
        ),
        storage={0x0: 0x60A7, 0x1: 0x60A7, 0x2: 0x60A7},
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x553E6C30AF61E7A3576F31311EA8A620F80D047E,
                        1: 0x1777F,
                        2: 0xD956C0ABD597440481902014A37B733358EE7685461EB1B5916EEFD83381E6D9,  # noqa: E501
                    }
                )
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x595C5D0C272757CFF0B3DCA4ED60D60CD6E9F58,
                        1: 0x177C9,
                        2: 0xD956C0ABD597440481902014A37B733358EE7685461EB1B5916EEFD83381E6D9,  # noqa: E501
                    }
                )
            },
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract: Account(storage={0: 0, 1: 44927, 2: 0})},
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract: Account(storage={0: 0, 1: 45001, 2: 0})},
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x553E6C30AF61E7A3576F31311EA8A620F80D047E,
                        1: 0x4BBCE4,
                        2: 0xDCBCC213F0C91B71D38DEDD06C95CCB99467B9B05F275BED536DE1044F5F18FA,  # noqa: E501
                    }
                )
            },
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract: Account(
                    storage={
                        0: 0xA5DC71D47D0D8DCF5990E81C74E981BAF24A8FA2,
                        1: 0x4BBD2E,
                        2: 0xDCBCC213F0C91B71D38DEDD06C95CCB99467B9B05F275BED536DE1044F5F18FA,  # noqa: E501
                    }
                )
            },
        },
        {
            "indexes": {"data": [6], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract: Account(storage={0: 0, 1: 48356, 2: 0})},
        },
        {
            "indexes": {"data": [7], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract: Account(storage={0: 0, 1: 48430, 2: 0})},
        },
        {
            "indexes": {"data": [8], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract: Account(storage={0: 0, 1: 0x4B16491, 2: 0})},
        },
        {
            "indexes": {"data": [9], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract: Account(storage={0: 0, 1: 0x4B16492, 2: 0})},
        },
        {
            "indexes": {"data": [10], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract: Account(storage={0: 0, 1: 48362, 2: 0})},
        },
        {
            "indexes": {"data": [11], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract: Account(storage={0: 0, 1: 48436, 2: 0})},
        },
        {
            "indexes": {"data": [12], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract: Account(storage={0: 0, 1: 0x4B1649D, 2: 0})},
        },
        {
            "indexes": {"data": [13], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract: Account(storage={0: 0, 1: 0x4B1649E, 2: 0})},
        },
        {
            "indexes": {"data": [14], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract: Account(storage={0: 0, 1: 54116, 2: 0})},
        },
        {
            "indexes": {"data": [15], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {contract: Account(storage={0: 0, 1: 54190, 2: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=1,
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
