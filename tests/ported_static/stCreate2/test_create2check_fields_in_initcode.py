"""
Check opcode values in create2 init code. Create2 called with different...

Ported from:
state_tests/stCreate2/create2checkFieldsInInitcodeFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
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
    ["state_tests/stCreate2/create2checkFieldsInInitcodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5",
        ),
        pytest.param(
            6,
            0,
            0,
            id="d6",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2check_fields_in_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Check opcode values in create2 init code."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_1 = Address(0x1000000000000000000000000000000000000000)
    contract_2 = Address(0x1100000000000000000000000000000000000000)
    contract_3 = Address(0x2000000000000000000000000000000000000000)
    contract_4 = Address(0x2200000000000000000000000000000000000000)
    contract_5 = Address(0x3000000000000000000000000000000000000000)
    contract_6 = Address(0x3300000000000000000000000000000000000000)
    contract_7 = Address(0x4000000000000000000000000000000000000000)
    contract_8 = Address(0x4400000000000000000000000000000000000000)
    contract_9 = Address(0xF000000000000000000000000000000000000000)
    contract_10 = Address(0xF200000000000000000000000000000000000000)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x56BC75E2D63100000)
    # Source: lll
    # { (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=Op.GAS,
            address=Op.CALLDATALOAD(offset=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )
    # Source: lll
    # { (CALL (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0 0) }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=Op.GAS,
            address=0xF000000000000000000000000000000000000000,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (CREATE2 0 0 (lll (seq (CALL (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0 0) (STOP) ) 0) 0) (STOP) }  # noqa: E501
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.PUSH1[0x24]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xF000000000000000000000000000000000000000,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.STOP * 2,
        nonce=0,
        address=Address(0x1100000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (CALLCODE (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0 0) }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=Op.GAS,
            address=0xF000000000000000000000000000000000000000,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x2000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (CREATE2 0 0 (lll (seq (CALLCODE (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0 0) (STOP) ) 0) 0)  (STOP) }  # noqa: E501
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.PUSH1[0x24]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.POP(
            Op.CALLCODE(
                gas=Op.GAS,
                address=0xF000000000000000000000000000000000000000,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.STOP * 2,
        nonce=0,
        address=Address(0x2200000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (DELEGATECALL (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0) (STOP) }  # noqa: E501
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=0xF000000000000000000000000000000000000000,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.STOP * 2,
        nonce=0,
        address=Address(0x3000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (CREATE2 0 0 (lll (seq (DELEGATECALL (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0) (STOP) ) 0) 0) (STOP) }  # noqa: E501
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.PUSH1[0x22]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=0xF000000000000000000000000000000000000000,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.STOP * 2,
        nonce=0,
        address=Address(0x3300000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (STATICCALL (GAS) 0xf200000000000000000000000000000000000000 0 0 0 256) [[10]] (MLOAD 0) }  # noqa: E501
    contract_7 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=0xF200000000000000000000000000000000000000,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x100,
            )
        )
        + Op.SSTORE(key=0xA, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        nonce=0,
        address=Address(0x4000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (CREATE2 0 0 (lll (seq (STATICCALL (GAS) 0xf200000000000000000000000000000000000000 0 0 0 256) [[10]] (MLOAD 0)  (STOP) ) 0) 0 ) }  # noqa: E501
    contract_8 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.PUSH1[0x29]
        + Op.CODECOPY(dest_offset=0x0, offset=0x11, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.CREATE2
        + Op.STOP
        + Op.INVALID
        + Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=0xF200000000000000000000000000000000000000,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x100,
            )
        )
        + Op.SSTORE(key=0xA, value=Op.MLOAD(offset=0x0))
        + Op.STOP * 2,
        nonce=0,
        address=Address(0x4400000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (CREATE2 0 0 (lll (seq   [[0]] (ADDRESS) [[1]] (BALANCE (ADDRESS)) [[2]] (ORIGIN) [[3]] (CALLER) [[4]] (CALLVALUE) [[5]] (CALLDATASIZE) [[6]] (CODESIZE) [[7]] (GASPRICE) (STOP)   ) 0) 0) (STOP) }  # noqa: E501
    contract_9 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.PUSH1[0x23]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.STOP * 2
        + Op.INVALID
        + Op.SSTORE(key=0x0, value=Op.ADDRESS)
        + Op.SSTORE(key=0x1, value=Op.BALANCE(address=Op.ADDRESS))
        + Op.SSTORE(key=0x2, value=Op.ORIGIN)
        + Op.SSTORE(key=0x3, value=Op.CALLER)
        + Op.SSTORE(key=0x4, value=Op.CALLVALUE)
        + Op.SSTORE(key=0x5, value=Op.CALLDATASIZE)
        + Op.SSTORE(key=0x6, value=Op.CODESIZE)
        + Op.SSTORE(key=0x7, value=Op.GASPRICE)
        + Op.STOP * 2,
        nonce=0,
        address=Address(0xF000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (CREATE2 0 0 (lll (seq   [0] (ADDRESS) [32] (BALANCE (ADDRESS)) [64] (ORIGIN) [96] (CALLER) [128] (CALLVALUE) [160] (CALLDATASIZE) [192] (CODESIZE) [224] (GASPRICE) (RETURN 0 256)  (STOP)   ) 0) 0)  }  # noqa: E501
    contract_10 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.PUSH1[0x29]
        + Op.CODECOPY(dest_offset=0x0, offset=0x11, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.CREATE2
        + Op.STOP
        + Op.INVALID
        + Op.MSTORE(offset=0x0, value=Op.ADDRESS)
        + Op.MSTORE(offset=0x20, value=Op.BALANCE(address=Op.ADDRESS))
        + Op.MSTORE(offset=0x40, value=Op.ORIGIN)
        + Op.MSTORE(offset=0x60, value=Op.CALLER)
        + Op.MSTORE(offset=0x80, value=Op.CALLVALUE)
        + Op.MSTORE(offset=0xA0, value=Op.CALLDATASIZE)
        + Op.MSTORE(offset=0xC0, value=Op.CODESIZE)
        + Op.MSTORE(offset=0xE0, value=Op.GASPRICE)
        + Op.RETURN(offset=0x0, size=0x100)
        + Op.STOP * 2,
        nonce=0,
        address=Address(0xF200000000000000000000000000000000000000),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(0xDAF9F53E732F21FE517E624B6DFE92DC8D0E51E0): Account(
                    storage={
                        0: 0xDAF9F53E732F21FE517E624B6DFE92DC8D0E51E0,
                        1: 0,
                        2: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        3: 0xF000000000000000000000000000000000000000,
                        4: 0,
                        5: 0,
                        6: 35,
                        7: 10,
                    },
                    balance=0,
                    nonce=1,
                ),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(0xDFAD1C567F12D848FABB8D9D8872C42E7AA81E95): Account(
                    storage={
                        0: 0xDFAD1C567F12D848FABB8D9D8872C42E7AA81E95,
                        1: 0,
                        2: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        3: 0x2000000000000000000000000000000000000000,
                        4: 0,
                        5: 0,
                        6: 35,
                        7: 10,
                    },
                    balance=0,
                    nonce=1,
                ),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": 2, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(0x3FF16480055C6CCC070257C61FA902448F4AE111): Account(
                    storage={
                        0: 0x3FF16480055C6CCC070257C61FA902448F4AE111,
                        1: 0,
                        2: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        3: 0x3000000000000000000000000000000000000000,
                        4: 0,
                        5: 0,
                        6: 35,
                        7: 10,
                    },
                    balance=0,
                    nonce=1,
                ),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": [3, 7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {sender: Account(nonce=1)},
        },
        {
            "indexes": {"data": 5, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(0x7CE21E3C16D63738CBBB697C919555C910504278): Account(
                    storage={
                        0: 0x7CE21E3C16D63738CBBB697C919555C910504278,
                        1: 0,
                        2: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        3: 0x9D25FBABDEB081B9ECD0645B9B6ABA8C7EB3821D,
                        4: 0,
                        5: 0,
                        6: 35,
                        7: 10,
                    },
                    balance=0,
                    nonce=1,
                ),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": 6, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(0xBB1B88EA45D33397F45583CA612ADEA3EB267318): Account(
                    storage={
                        0: 0xBB1B88EA45D33397F45583CA612ADEA3EB267318,
                        1: 0,
                        2: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        3: 0x45DDE7FBF9F1CF09E18C4E584BA93C82E83C8898,
                        4: 0,
                        5: 0,
                        6: 35,
                        7: 10,
                    },
                    balance=0,
                    nonce=1,
                ),
                sender: Account(nonce=1),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(contract_1, left_padding=True),
        Hash(contract_3, left_padding=True),
        Hash(contract_5, left_padding=True),
        Hash(contract_7, left_padding=True),
        Hash(contract_2, left_padding=True),
        Hash(contract_4, left_padding=True),
        Hash(contract_6, left_padding=True),
        Hash(contract_8, left_padding=True),
    ]
    tx_gas = [600000]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
