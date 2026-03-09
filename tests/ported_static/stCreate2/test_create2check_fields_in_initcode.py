"""
Check opcode values in create2 init code. Create2 called with different...

Ported from:
tests/static/state_tests/stCreate2/create2checkFieldsInInitcodeFiller.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCreate2/create2checkFieldsInInitcodeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "0000000000000000000000001000000000000000000000000000000000000000",
            {
                Address("0xdaf9f53e732f21fe517e624b6dfe92dc8d0e51e0"): Account(
                    storage={
                        0: 0xDAF9F53E732F21FE517E624B6DFE92DC8D0E51E0,
                        2: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        3: 0xF000000000000000000000000000000000000000,
                        6: 35,
                        7: 10,
                    }
                )
            },
        ),
        (
            "0000000000000000000000002000000000000000000000000000000000000000",
            {
                Address("0xdfad1c567f12d848fabb8d9d8872c42e7aa81e95"): Account(
                    storage={
                        0: 0xDFAD1C567F12D848FABB8D9D8872C42E7AA81E95,
                        2: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        3: 0x2000000000000000000000000000000000000000,
                        6: 35,
                        7: 10,
                    }
                )
            },
        ),
        (
            "0000000000000000000000003000000000000000000000000000000000000000",
            {
                Address("0x3ff16480055c6ccc070257c61fa902448f4ae111"): Account(
                    storage={
                        0: 0x3FF16480055C6CCC070257C61FA902448F4AE111,
                        2: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        3: 0x3000000000000000000000000000000000000000,
                        6: 35,
                        7: 10,
                    }
                )
            },
        ),
        (
            "0000000000000000000000004000000000000000000000000000000000000000",
            {},
        ),
        (
            "0000000000000000000000001100000000000000000000000000000000000000",
            {
                Address("0xdaf9f53e732f21fe517e624b6dfe92dc8d0e51e0"): Account(
                    storage={
                        0: 0xDAF9F53E732F21FE517E624B6DFE92DC8D0E51E0,
                        2: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        3: 0xF000000000000000000000000000000000000000,
                        6: 35,
                        7: 10,
                    }
                )
            },
        ),
        (
            "0000000000000000000000002200000000000000000000000000000000000000",
            {
                Address("0x7ce21e3c16d63738cbbb697c919555c910504278"): Account(
                    storage={
                        0: 0x7CE21E3C16D63738CBBB697C919555C910504278,
                        2: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        3: 0x9D25FBABDEB081B9ECD0645B9B6ABA8C7EB3821D,
                        6: 35,
                        7: 10,
                    }
                )
            },
        ),
        (
            "0000000000000000000000003300000000000000000000000000000000000000",
            {
                Address("0xbb1b88ea45d33397f45583ca612adea3eb267318"): Account(
                    storage={
                        0: 0xBB1B88EA45D33397F45583CA612ADEA3EB267318,
                        2: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        3: 0x45DDE7FBF9F1CF09E18C4E584BA93C82E83C8898,
                        6: 35,
                        7: 10,
                    }
                )
            },
        ),
        (
            "0000000000000000000000004400000000000000000000000000000000000000",
            {},
        ),
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2check_fields_in_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Check opcode values in create2 init code. Create2 called with..."""
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
        gas_limit=1000000,
    )

    # Source: LLL
    # { (CALL (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0 0) }
    pre.deploy_contract(
        code=(
            Op.CALL(
                gas=Op.GAS,
                address=0xF000000000000000000000000000000000000000,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { (CREATE2 0 0 (lll (seq (CALL (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0 0) (STOP) ) 0) 0) (STOP) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH1[0x24]
            + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.CREATE2)
            + Op.STOP
            + Op.STOP
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
                ),
            )
            + Op.STOP
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1100000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { (CALLCODE (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0 0) }
    pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=Op.GAS,
                address=0xF000000000000000000000000000000000000000,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x2000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { (CREATE2 0 0 (lll (seq (CALLCODE (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0 0) (STOP) ) 0) 0)  (STOP) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH1[0x24]
            + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.CREATE2)
            + Op.STOP
            + Op.STOP
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
                ),
            )
            + Op.STOP
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x2200000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { (DELEGATECALL (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0) (STOP) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.DELEGATECALL(
                    gas=Op.GAS,
                    address=0xF000000000000000000000000000000000000000,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x3000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { (CREATE2 0 0 (lll (seq (DELEGATECALL (GAS) 0xf000000000000000000000000000000000000000 0 0 0 0) (STOP) ) 0) 0) (STOP) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH1[0x22]
            + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.CREATE2)
            + Op.STOP
            + Op.STOP
            + Op.INVALID
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.GAS,
                    address=0xF000000000000000000000000000000000000000,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x3300000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { (STATICCALL (GAS) 0xf200000000000000000000000000000000000000 0 0 0 256) [[10]] (MLOAD 0) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=Op.GAS,
                    address=0xF200000000000000000000000000000000000000,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x100,
                ),
            )
            + Op.SSTORE(key=0xA, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x4000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { (CREATE2 0 0 (lll (seq (STATICCALL (GAS) 0xf200000000000000000000000000000000000000 0 0 0 256) [[10]] (MLOAD 0)  (STOP) ) 0) 0 ) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH1[0x29]
            + Op.CODECOPY(dest_offset=0x0, offset=0x11, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
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
                ),
            )
            + Op.SSTORE(key=0xA, value=Op.MLOAD(offset=0x0))
            + Op.STOP
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x4400000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x56BC75E2D63100000)
    # Source: LLL
    # { (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: LLL
    # { (CREATE2 0 0 (lll (seq   [[0]] (ADDRESS) [[1]] (BALANCE (ADDRESS)) [[2]] (ORIGIN) [[3]] (CALLER) [[4]] (CALLVALUE) [[5]] (CALLDATASIZE) [[6]] (CODESIZE) [[7]] (GASPRICE) (STOP)   ) 0) 0) (STOP) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH1[0x23]
            + Op.CODECOPY(dest_offset=0x0, offset=0x13, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.CREATE2)
            + Op.STOP
            + Op.STOP
            + Op.INVALID
            + Op.SSTORE(key=0x0, value=Op.ADDRESS)
            + Op.SSTORE(key=0x1, value=Op.BALANCE(address=Op.ADDRESS))
            + Op.SSTORE(key=0x2, value=Op.ORIGIN)
            + Op.SSTORE(key=0x3, value=Op.CALLER)
            + Op.SSTORE(key=0x4, value=Op.CALLVALUE)
            + Op.SSTORE(key=0x5, value=Op.CALLDATASIZE)
            + Op.SSTORE(key=0x6, value=Op.CODESIZE)
            + Op.SSTORE(key=0x7, value=Op.GASPRICE)
            + Op.STOP
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xf000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { (CREATE2 0 0 (lll (seq   [0] (ADDRESS) [32] (BALANCE (ADDRESS)) [64] (ORIGIN) [96] (CALLER) [128] (CALLVALUE) [160] (CALLDATASIZE) [192] (CODESIZE) [224] (GASPRICE) (RETURN 0 256)  (STOP)   ) 0) 0)  }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH1[0x29]
            + Op.CODECOPY(dest_offset=0x0, offset=0x11, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
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
            + Op.STOP
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xf200000000000000000000000000000000000000"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=600000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
