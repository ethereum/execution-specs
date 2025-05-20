"""test `CALLDATACOPY` opcode."""

import pytest

from ethereum_test_forks import Byzantium, Fork
from ethereum_test_tools import Account, Alloc, Bytecode, StateTestFiller, Transaction
from ethereum_test_tools.vm.opcode import Opcodes as Op


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/VMTests/vmTests/calldatacopyFiller.yml",
    ],
    pr=["https://github.com/ethereum/execution-spec-tests/pull/1056"],
)
@pytest.mark.parametrize(
    "code,tx_data,code_address_storage,to_address_storage",
    [
        (
            (
                Op.CALLDATACOPY(dest_offset=0, offset=1, size=2)
                + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0))
                + Op.RETURN(offset=0, size=Op.MSIZE)
            ),
            b"\x00",
            Account(
                storage={0x00: 0x3456000000000000000000000000000000000000000000000000000000000000}
            ),
            Account(
                storage={0x00: 0x3456000000000000000000000000000000000000000000000000000000000000}
            ),
        ),
        (
            (
                Op.CALLDATACOPY(dest_offset=0, offset=1, size=1)
                + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0))
                + Op.RETURN(offset=0, size=Op.MSIZE)
            ),
            b"\x01",
            Account(
                storage={0x00: 0x3400000000000000000000000000000000000000000000000000000000000000},
            ),
            Account(
                storage={0x00: 0x3400000000000000000000000000000000000000000000000000000000000000},
            ),
        ),
        (
            (
                Op.CALLDATACOPY(dest_offset=0, offset=1, size=0)
                + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0))
                + Op.RETURN(offset=0, size=Op.MSIZE)
            ),
            b"\x02",
            Account(
                storage={0x00: 0x00},
            ),
            Account(
                storage={0x00: 0x00},
            ),
        ),
        (
            (
                Op.CALLDATACOPY(dest_offset=0, offset=0, size=0)
                + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0))
                + Op.RETURN(offset=0, size=Op.MSIZE)
            ),
            b"\x03",
            Account(
                storage={0x00: 0x00},
            ),
            Account(
                storage={0x00: 0x00},
            ),
        ),
        (
            (
                Op.CALLDATACOPY(
                    dest_offset=0,
                    offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFA,
                    size=0xFF,
                )
                + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0))
                + Op.RETURN(offset=0, size=Op.MSIZE)
            ),
            b"\x04",
            Account(storage={0x00: 0x00}),
            Account(storage={0x00: 0x00}),
        ),
        (
            (
                Op.CALLDATACOPY(
                    dest_offset=0,
                    offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFA,
                    size=0x9,
                )
                + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0))
                + Op.RETURN(offset=0, size=Op.MSIZE)
            ),
            b"\x05",
            Account(storage={0x00: 0x00}),
            Account(storage={0x00: 0x00}),
        ),
        (
            (Op.SSTORE(key=0x1, value=0x1) + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.CALLDATACOPY),
            b"\x10",
            Account(storage={0x01: 0x00}),
            None,
        ),
        (
            (
                Op.JUMP(pc=0x5)
                + Op.JUMPDEST
                + Op.STOP
                + Op.JUMPDEST
                + Op.MSTORE8(offset=0x1F, value=0x42)
                + Op.CALLDATACOPY(dest_offset=0x1F, offset=0x0, size=0x103)
                + Op.MLOAD(offset=0x0)
                + Op.DUP1
                + Op.PUSH1[0x60]
                + Op.JUMPI(pc=0x3, condition=Op.EQ)
                + Op.SSTORE(key=0xFF, value=0xBADC0FFEE)
            ),
            b"\x11",
            Account(storage={0xFF: 0xBADC0FFEE}),
            None,
        ),
    ],
    ids=[
        "cdc 0 1 2",
        "cdc 0 1 1",
        "cdc 0 1 0",
        "cdc 0 0 0",
        "cdc 0 neg6 ff",
        "cdc 0 neg6 9",
        "underflow",
        "sec",
    ],
)
def test_calldatacopy(
    state_test: StateTestFiller,
    code: Bytecode,
    fork: Fork,
    tx_data: bytes,
    pre: Alloc,
    code_address_storage: Account,
    to_address_storage: Account | None,
):
    """
    Test `CALLDATACOPY` opcode.

    Based on https://github.com/ethereum/tests/blob/ae4791077e8fcf716136e70fe8392f1a1f1495fb/src/GeneralStateTestsFiller/VMTests/vmTests/calldatacopyFiller.yml
    """
    code_address = pre.deploy_contract(code)
    to = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x1234567890ABCDEF01234567890ABCDEF0)
            + Op.CALL(
                gas=Op.SUB(Op.GAS(), 0x100),
                address=code_address,
                value=0x0,
                args_offset=0xF,
                args_size=0x10,
                ret_offset=0x20,
                ret_size=0x40,
            )
            + Op.POP
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x20))
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x40))
            + Op.STOP
        ),
    )

    tx = Transaction(
        data=tx_data,
        gas_limit=100_000,
        gas_price=0x0A,
        protected=fork >= Byzantium,
        sender=pre.fund_eoa(),
        to=to,
        value=0x01,
    )
    if to_address_storage:
        post = {code_address: code_address_storage, to: to_address_storage}
    else:
        post = {code_address: code_address_storage}
    state_test(pre=pre, post=post, tx=tx)
