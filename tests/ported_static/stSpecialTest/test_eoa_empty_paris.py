"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSpecialTest/eoaEmptyParisFiller.yml
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
    TransactionException,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stSpecialTest/eoaEmptyParisFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value, tx_error, expected_post",
    [
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            10000000,
            0,
            None,
            {
                Address("0x000000000000000000000000000000000000bad4"): Account(
                    storage={57005: 48879}
                ),
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={
                        0: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        63: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        241: 118,
                        255: 7626,
                        47825: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47826: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47827: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47828: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                    }
                ),
            },
            id="case0",
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            10000000,
            100,
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            {
                Address("0x000000000000000000000000000000000000bad4"): Account(
                    storage={57005: 48879}
                )
            },
            id="case1",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            9999999,
            0,
            None,
            {
                Address("0x000000000000000000000000000000000000bad4"): Account(
                    storage={57005: 48879}
                ),
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={
                        0: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        49: 100,
                        63: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        241: 118,
                        255: 7626,
                        47825: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47826: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47827: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47828: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                    }
                ),
            },
            id="case2",
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            9999999,
            100,
            None,
            {
                Address("0x000000000000000000000000000000000000bad4"): Account(
                    storage={57005: 48879}
                ),
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={
                        0: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        63: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        241: 118,
                        255: 7626,
                        47825: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47826: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47827: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47828: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                    }
                ),
            },
            id="case3",
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            10000000,
            0,
            None,
            {
                Address("0x000000000000000000000000000000000000bad4"): Account(
                    storage={57005: 48879}
                ),
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={
                        0: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        63: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        241: 6818,
                        255: 7626,
                        47825: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47826: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47827: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47828: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                    }
                ),
            },
            id="case4",
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            10000000,
            100,
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            {
                Address("0x000000000000000000000000000000000000bad4"): Account(
                    storage={57005: 48879}
                )
            },
            id="case5",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            9999999,
            0,
            None,
            {
                Address("0x000000000000000000000000000000000000bad4"): Account(
                    storage={57005: 48879}
                ),
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={
                        0: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        49: 100,
                        63: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        241: 6818,
                        255: 7626,
                        47825: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47826: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47827: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47828: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                    }
                ),
            },
            id="case6",
        ),
        pytest.param(
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            9999999,
            100,
            None,
            {
                Address("0x000000000000000000000000000000000000bad4"): Account(
                    storage={57005: 48879}
                ),
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={
                        0: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        63: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        241: 6818,
                        255: 7626,
                        47825: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47826: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47827: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                        47828: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                    }
                ),
            },
            id="case7",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_eoa_empty_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    tx_value: int,
    tx_error: object,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )
    callee = Address("0x000000000000000000000000000000000000bad1")
    callee_1 = Address("0x000000000000000000000000000000000000bad2")
    callee_2 = Address("0x000000000000000000000000000000000000bad3")
    callee_3 = Address("0x000000000000000000000000000000000000bad4")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=0, nonce=1)
    pre[callee_2] = Account(balance=1, nonce=1)
    pre[callee_3] = Account(balance=10, nonce=0, storage={0xDEAD: 0xBEEF})
    # Source: Yul
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
    contract = pre.deploy_contract(
        code=(
            Op.ORIGIN
            + Op.SSTORE(key=0x0, value=Op.DUP1)
            + Op.SSTORE(key=0x31, value=Op.BALANCE(address=Op.DUP1))
            + Op.SSTORE(key=0x3B, value=Op.EXTCODESIZE(address=Op.DUP1))
            + Op.SSTORE(key=0x3F, value=Op.EXTCODEHASH(address=Op.DUP1))
            + Op.SSTORE(
                key=0x13F,
                value=Op.EXTCODEHASH(address=Op.ADD(Op.DUP2, 0x1)),
            )
            + Op.SSTORE(key=0xBAD1, value=Op.EXTCODEHASH(address=0xBAD1))
            + Op.SSTORE(key=0xBAD2, value=Op.EXTCODEHASH(address=0xBAD2))
            + Op.SSTORE(key=0xBAD3, value=Op.EXTCODEHASH(address=0xBAD3))
            + Op.SSTORE(key=0xBAD4, value=Op.EXTCODEHASH(address=0xBAD4))
            + Op.SSTORE(key=0xBAD5, value=Op.EXTCODEHASH(address=0xBAD5))
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
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
                ),
            )
            + Op.GAS
            + Op.SWAP1
            + Op.SSTORE(key=0xFF, value=Op.SUB)
            + Op.STOP
        ),
        address=Address("0x000000000000000000000000000000000000c0de"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    selfdestruct(origin())
    # }
    pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=Op.ORIGIN),
        balance=0x2710,
        address=Address("0x000000000000000000000000000000000000dead"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3B9ACA00)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        gas_price=100,
        value=tx_value,
        error=tx_error,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
