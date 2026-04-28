"""
Test_eoa_empty_paris.

Ported from:
state_tests/stSpecialTest/eoaEmptyParisFiller.yml
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
    TransactionException,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSpecialTest/eoaEmptyParisFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-g0-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="d0-g0-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0,
            1,
            0,
            id="d0-g1-v0",
        ),
        pytest.param(
            0,
            1,
            1,
            id="d0-g1-v1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-g0-v0",
        ),
        pytest.param(
            1,
            0,
            1,
            id="d1-g0-v1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            1,
            1,
            0,
            id="d1-g1-v0",
        ),
        pytest.param(
            1,
            1,
            1,
            id="d1-g1-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_eoa_empty_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_eoa_empty_paris."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x000000000000000000000000000000000000BAD1)
    contract_1 = Address(0x000000000000000000000000000000000000BAD2)
    contract_2 = Address(0x000000000000000000000000000000000000BAD3)
    contract_3 = Address(0x000000000000000000000000000000000000BAD4)
    contract_4 = Address(0x000000000000000000000000000000000000DEAD)
    contract_5 = Address(0x000000000000000000000000000000000000C0DE)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[sender] = Account(balance=0x3B9ACA00)
    # Source: hex
    # 0x
    contract_0 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=1,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000BAD1),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_1 = pre.deploy_contract(  # noqa: F841
        code="",
        nonce=1,
        address=Address(0x000000000000000000000000000000000000BAD2),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_2 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=1,
        nonce=1,
        address=Address(0x000000000000000000000000000000000000BAD3),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_3 = pre.deploy_contract(  # noqa: F841
        code="",
        storage={57005: 48879},
        balance=10,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000BAD4),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    selfdestruct(origin())
    # }
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=Op.ORIGIN),
        balance=10000,
        nonce=1,
        address=Address(0x000000000000000000000000000000000000DEAD),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    let eoa := origin()   // external owner account
    #    sstore(0, eoa)
    #    sstore(0x31, balance(eoa))   // balance at this point, where it is assumed we used gasLimit gas  # noqa: E501
    #    sstore(0x3B, extcodesize(eoa))
    #    sstore(0x3F, extcodehash(eoa))
    #    sstore(0x013F, extcodehash(add(eoa, 0x1)))
    #    sstore(0xBAD1, extcodehash(0xBAD1))
    #    sstore(0xBAD2, extcodehash(0xBAD2))
    #    sstore(0xBAD3, extcodehash(0xBAD3))
    #    sstore(0xBAD4, extcodehash(0xBAD4))
    #    sstore(0xBAD5, extcodehash(0xBAD5))
    #
    #    // The gas cost of calling the EOA (it should be warm)
    #    let gas0 := gas()
    #    pop(call(gas(), eoa, calldataload(4), 0, 0, 0, 0))
    #    sstore(0xF1, sub(gas0, gas()))
    #
    #    // Gas cost of selfdestruct going to the EOA (should also be warm)
    #    gas0 := gas()
    #    pop(call(gas(), 0xDEAD, 0, 0, 0, 0, 0))
    #    sstore(0xFF, sub(gas0, gas()))
    # }
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.ORIGIN
        + Op.SSTORE(key=0x0, value=Op.DUP1)
        + Op.SSTORE(key=0x31, value=Op.BALANCE(address=Op.DUP1))
        + Op.SSTORE(key=0x3B, value=Op.EXTCODESIZE(address=Op.DUP1))
        + Op.SSTORE(key=0x3F, value=Op.EXTCODEHASH(address=Op.DUP1))
        + Op.SSTORE(
            key=0x13F, value=Op.EXTCODEHASH(address=Op.ADD(Op.DUP2, 0x1))
        )
        + Op.SSTORE(key=0xBAD1, value=Op.EXTCODEHASH(address=0xBAD1))
        + Op.SSTORE(key=0xBAD2, value=Op.EXTCODEHASH(address=0xBAD2))
        + Op.SSTORE(key=0xBAD3, value=Op.EXTCODEHASH(address=0xBAD3))
        + Op.SSTORE(key=0xBAD4, value=Op.EXTCODEHASH(address=0xBAD4))
        + Op.SSTORE(key=0xBAD5, value=Op.EXTCODEHASH(address=0xBAD5))
        + Op.PUSH1[0x0]
        + Op.DUP1 * 3
        + Op.GAS
        + Op.SWAP5
        + Op.CALLDATALOAD(offset=0x4)
        + Op.SWAP1
        + Op.GAS
        + Op.POP(Op.CALL)
        + Op.GAS
        + Op.SWAP1
        + Op.SSTORE(key=0xF1, value=Op.SUB)
        + Op.GAS
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xDEAD,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.GAS
        + Op.SWAP1
        + Op.SSTORE(key=0xFF, value=Op.SUB)
        + Op.STOP,
        nonce=1,
        address=Address(0x000000000000000000000000000000000000C0DE),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_5: Account(
                    storage={
                        0: sender,
                        49: 0,
                        59: 0,
                        63: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        241: 118,
                        255: 7626,
                        319: 0,
                        47825: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47826: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47827: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47828: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_5: Account(
                    storage={
                        0: sender,
                        49: 0,
                        59: 0,
                        63: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        241: 6818,
                        255: 7626,
                        319: 0,
                        47825: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47826: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47827: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47828: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": -1, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_5: Account(
                    storage={
                        0: sender,
                        49: 100,
                        59: 0,
                        63: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        241: 118,
                        255: 7626,
                        319: 0,
                        47825: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47826: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47827: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47828: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_5: Account(
                    storage={
                        0: sender,
                        49: 100,
                        59: 0,
                        63: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        241: 6818,
                        255: 7626,
                        319: 0,
                        47825: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47826: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47827: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47828: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": 1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_5: Account(
                    storage={
                        0: sender,
                        49: 0,
                        59: 0,
                        63: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        241: 118,
                        255: 7626,
                        319: 0,
                        47825: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47826: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47827: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47828: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_5: Account(
                    storage={
                        0: sender,
                        49: 0,
                        59: 0,
                        63: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        241: 6818,
                        255: 7626,
                        319: 0,
                        47825: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47826: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47827: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47828: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x1),
    ]
    tx_gas = [10000000, 9999999]
    tx_value = [0, 100]

    tx = Transaction(
        sender=sender,
        to=contract_5,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        gas_price=100,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
