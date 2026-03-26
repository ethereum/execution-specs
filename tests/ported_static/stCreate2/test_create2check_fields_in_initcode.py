"""
Check opcode values in create2 init code. Create2 called with different call types. CREATE2 inside CRETE2 inside CALL, CALLCODE, DELEGATECALL, STATICCALL << test values of  SENDER,address and so on.

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
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "0000000000000000000000001000000000000000000000000000000000000000",
    "0000000000000000000000002000000000000000000000000000000000000000",
    "0000000000000000000000003000000000000000000000000000000000000000",
    "0000000000000000000000004000000000000000000000000000000000000000",
    "0000000000000000000000001100000000000000000000000000000000000000",
    "0000000000000000000000002200000000000000000000000000000000000000",
    "0000000000000000000000003300000000000000000000000000000000000000",
    "0000000000000000000000004400000000000000000000000000000000000000",
]
TX_GAS = [600000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2checkFieldsInInitcodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="d0",
        ),
        pytest.param(
            1, 0, 0,
            id="d1",
        ),
        pytest.param(
            2, 0, 0,
            id="d2",
        ),
        pytest.param(
            3, 0, 0,
            id="d3",
        ),
        pytest.param(
            4, 0, 0,
            id="d4",
        ),
        pytest.param(
            5, 0, 0,
            id="d5",
        ),
        pytest.param(
            6, 0, 0,
            id="d6",
        ),
        pytest.param(
            7, 0, 0,
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
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_1 = Address("0x1000000000000000000000000000000000000000")
    contract_2 = Address("0x1100000000000000000000000000000000000000")
    contract_3 = Address("0x2000000000000000000000000000000000000000")
    contract_4 = Address("0x2200000000000000000000000000000000000000")
    contract_5 = Address("0x3000000000000000000000000000000000000000")
    contract_6 = Address("0x3300000000000000000000000000000000000000")
    contract_7 = Address("0x4000000000000000000000000000000000000000")
    contract_8 = Address("0x4400000000000000000000000000000000000000")
    contract_9 = Address("0xf000000000000000000000000000000000000000")
    contract_10 = Address("0xf200000000000000000000000000000000000000")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x56bc75e2d63100000)
    # Source: lll
    # { (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    contract_0 = pre.deploy_contract(
        code=Op.CALL(gas=Op.GAS, address=Op.CALLDATALOAD(offset=0x0), value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: lll
    # { (CALL (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0 0) }
    contract_1 = pre.deploy_contract(
        code=Op.CALL(gas=Op.GAS, address=0xf000000000000000000000000000000000000000, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # { (CREATE2 0 0 (lll (seq (CALL (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0 0) (STOP) ) 0) 0) (STOP) }
    contract_2 = pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.PUSH1[0x24]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2 + Op.POP(Op.CREATE2) + Op.STOP * 2 + Op.INVALID
        + Op.POP(Op.CALL(gas=Op.GAS, address=0xf000000000000000000000000000000000000000, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.STOP * 2,
        nonce=0,
        address=Address("0x1100000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # { (CALLCODE (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0 0) }
    contract_3 = pre.deploy_contract(
        code=Op.CALLCODE(gas=Op.GAS, address=0xf000000000000000000000000000000000000000, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0x2000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # { (CREATE2 0 0 (lll (seq (CALLCODE (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0 0) (STOP) ) 0) 0)  (STOP) }
    contract_4 = pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.PUSH1[0x24]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2 + Op.POP(Op.CREATE2) + Op.STOP * 2 + Op.INVALID
        + Op.POP(Op.CALLCODE(gas=Op.GAS, address=0xf000000000000000000000000000000000000000, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.STOP * 2,
        nonce=0,
        address=Address("0x2200000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # { (DELEGATECALL (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0) (STOP) }
    contract_5 = pre.deploy_contract(
        code=Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=0xf000000000000000000000000000000000000000, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.STOP * 2,
        nonce=0,
        address=Address("0x3000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # { (CREATE2 0 0 (lll (seq (DELEGATECALL (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0) (STOP) ) 0) 0) (STOP) }
    contract_6 = pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.PUSH1[0x22]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2 + Op.POP(Op.CREATE2) + Op.STOP * 2 + Op.INVALID
        + Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=0xf000000000000000000000000000000000000000, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.STOP * 2,
        nonce=0,
        address=Address("0x3300000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # { (STATICCALL (GAS) 0xf200000000000000000000000000000000000000 0 0 0 256) [[10]] (MLOAD 0) }
    contract_7 = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(gas=Op.GAS, address=0xf200000000000000000000000000000000000000, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x100))
        + Op.SSTORE(key=0xa, value=Op.MLOAD(offset=0x0)) + Op.STOP,
        nonce=0,
        address=Address("0x4000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # { (CREATE2 0 0 (lll (seq (STATICCALL (GAS) 0xf200000000000000000000000000000000000000 0 0 0 256) [[10]] (MLOAD 0)  (STOP) ) 0) 0 ) }
    contract_8 = pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.PUSH1[0x29]
        + Op.CODECOPY(dest_offset=0x0, offset=0x11, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2 + Op.CREATE2 + Op.STOP + Op.INVALID
        + Op.POP(Op.STATICCALL(gas=Op.GAS, address=0xf200000000000000000000000000000000000000, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x100))
        + Op.SSTORE(key=0xa, value=Op.MLOAD(offset=0x0)) + Op.STOP * 2,
        nonce=0,
        address=Address("0x4400000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # { (CREATE2 0 0 (lll (seq   [[0]] (ADDRESS) [[1]] (BALANCE (ADDRESS)) [[2]] (ORIGIN) [[3]] (CALLER) [[4]] (CALLVALUE) [[5]] (CALLDATASIZE) [[6]] (CODESIZE) [[7]] (GASPRICE) (STOP)   ) 0) 0) (STOP) }
    contract_9 = pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.PUSH1[0x23]
        + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2 + Op.POP(Op.CREATE2) + Op.STOP * 2 + Op.INVALID
        + Op.SSTORE(key=0x0, value=Op.ADDRESS)
        + Op.SSTORE(key=0x1, value=Op.BALANCE(address=Op.ADDRESS))
        + Op.SSTORE(key=0x2, value=Op.ORIGIN)
        + Op.SSTORE(key=0x3, value=Op.CALLER)
        + Op.SSTORE(key=0x4, value=Op.CALLVALUE)
        + Op.SSTORE(key=0x5, value=Op.CALLDATASIZE)
        + Op.SSTORE(key=0x6, value=Op.CODESIZE)
        + Op.SSTORE(key=0x7, value=Op.GASPRICE) + Op.STOP * 2,
        nonce=0,
        address=Address("0xf000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # { (CREATE2 0 0 (lll (seq   [0] (ADDRESS) [32] (BALANCE (ADDRESS)) [64] (ORIGIN) [96] (CALLER) [128] (CALLVALUE) [160] (CALLDATASIZE) [192] (CODESIZE) [224] (GASPRICE) (RETURN 0 256)  (STOP)   ) 0) 0)  }
    contract_10 = pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.PUSH1[0x29]
        + Op.CODECOPY(dest_offset=0x0, offset=0x11, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2 + Op.CREATE2 + Op.STOP + Op.INVALID
        + Op.MSTORE(offset=0x0, value=Op.ADDRESS)
        + Op.MSTORE(offset=0x20, value=Op.BALANCE(address=Op.ADDRESS))
        + Op.MSTORE(offset=0x40, value=Op.ORIGIN)
        + Op.MSTORE(offset=0x60, value=Op.CALLER)
        + Op.MSTORE(offset=0x80, value=Op.CALLVALUE)
        + Op.MSTORE(offset=0xa0, value=Op.CALLDATASIZE)
        + Op.MSTORE(offset=0xc0, value=Op.CODESIZE)
        + Op.MSTORE(offset=0xe0, value=Op.GASPRICE)
        + Op.RETURN(offset=0x0, size=0x100) + Op.STOP * 2,
        nonce=0,
        address=Address("0xf200000000000000000000000000000000000000"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 4], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        Address("0xdaf9f53e732f21fe517e624b6dfe92dc8d0e51e0"): Account(
                storage={
            0: 0xdaf9f53e732f21fe517e624b6dfe92dc8d0e51e0,
            1: 0,
            2: 0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b,
            3: 0xf000000000000000000000000000000000000000,
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
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        Address("0xdfad1c567f12d848fabb8d9d8872c42e7aa81e95"): Account(
                storage={
            0: 0xdfad1c567f12d848fabb8d9d8872c42e7aa81e95,
            1: 0,
            2: 0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b,
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
            "indexes": {'data': 2, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        Address("0x3ff16480055c6ccc070257c61fa902448f4ae111"): Account(
                storage={
            0: 0x3ff16480055c6ccc070257c61fa902448f4ae111,
            1: 0,
            2: 0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b,
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
            "indexes": {'data': [3, 7], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {sender: Account(nonce=1)},
        },
        {
            "indexes": {'data': 5, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        Address("0x7ce21e3c16d63738cbbb697c919555c910504278"): Account(
                storage={
            0: 0x7ce21e3c16d63738cbbb697c919555c910504278,
            1: 0,
            2: 0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b,
            3: 0x9d25fbabdeb081b9ecd0645b9b6aba8c7eb3821d,
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
            "indexes": {'data': 6, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        Address("0xbb1b88ea45d33397f45583ca612adea3eb267318"): Account(
                storage={
            0: 0xbb1b88ea45d33397f45583ca612adea3eb267318,
            1: 0,
            2: 0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b,
            3: 0x45dde7fbf9f1cf09e18c4e584ba93c82e83c8898,
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

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
