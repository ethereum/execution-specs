"""
Delegate calls CREATE/CREATE2 from an account with max allowed nonce/max...

Ported from:
tests/static/state_tests/stCreate2/CREATE2_HighNonceDelegatecallFiller.yml
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
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
]

TX_GAS = [16777216]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCreate2/CREATE2_HighNonceDelegatecallFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(14, 0, 0, id="case0"),
        pytest.param(2, 0, 0, id="case1"),
        pytest.param(15, 0, 0, id="case2"),
        pytest.param(3, 0, 0, id="case3"),
        pytest.param(16, 0, 0, id="case4"),
        pytest.param(4, 0, 0, id="case5"),
        pytest.param(17, 0, 0, id="case6"),
        pytest.param(5, 0, 0, id="case7"),
        pytest.param(12, 0, 0, id="case8"),
        pytest.param(0, 0, 0, id="case9"),
        pytest.param(13, 0, 0, id="case10"),
        pytest.param(1, 0, 0, id="case11"),
        pytest.param(20, 0, 0, id="case12"),
        pytest.param(8, 0, 0, id="case13"),
        pytest.param(21, 0, 0, id="case14"),
        pytest.param(9, 0, 0, id="case15"),
        pytest.param(22, 0, 0, id="case16"),
        pytest.param(10, 0, 0, id="case17"),
        pytest.param(23, 0, 0, id="case18"),
        pytest.param(11, 0, 0, id="case19"),
        pytest.param(18, 0, 0, id="case20"),
        pytest.param(6, 0, 0, id="case21"),
        pytest.param(19, 0, 0, id="case22"),
        pytest.param(7, 0, 0, id="case23"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2_high_nonce_delegatecall(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Delegate calls CREATE/CREATE2 from an account with max allowed..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
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
    callee = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x0)
            + Op.SLOAD(key=0xFFFF)
            + Op.MSTORE(offset=0x0, value=0x6005600C60003960056000F36001600155)
            + Op.PUSH1[0x0]
            + Op.SWAP2
            + Op.JUMPI(pc=0x5E, condition=Op.EQ(Op.DUP2, 0x0))
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.JUMPI(pc=0x4F, condition=Op.EQ)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x2, value=Op.DUP2)
            + Op.JUMPI(pc=0x43, condition=Op.GT(Op.DUP3, 0x0))
            + Op.JUMPDEST
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.MSTORE
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.SSTORE(key=0xFFFF, value=Op.ADD)
            + Op.CODESIZE
            + Op.JUMP(pc=0x39)
            + Op.JUMPDEST
            + Op.SWAP1
            + Op.POP
            + Op.CREATE2(value=0x0, offset=0xF, size=0x11, salt=Op.DUP1)
            + Op.SWAP1
            + Op.JUMP(pc=0x2D)
            + Op.JUMPDEST
            + Op.SWAP2
            + Op.POP
            + Op.PUSH1[0x1]
            + Op.CREATE(value=0x0, offset=0xF, size=0x11)
            + Op.SWAP3
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x26)
        ),
        storage={0xFFFF: 0xFFFFFFFFFFFFFFFE},
        nonce=18446744073709551614,
        address=Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"),  # noqa: E501
    )
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x4)
            + Op.CALLDATALOAD(offset=0x24)
            + Op.SWAP1
            + Op.CALLDATALOAD(offset=0x44)
            + Op.SWAP1
            + Op.CALLDATALOAD(offset=0x64)
            + Op.SLOAD(key=0xFFFF)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8B, condition=Op.LT(Op.DUP2, Op.DUP5))
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.MSTORE
            + Op.PUSH1[0x2]
            + Op.SWAP1
            + Op.JUMPI(pc=0x79, condition=Op.ISZERO(Op.DUP1))
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x66, condition=Op.EQ(Op.DUP2, 0x1))
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x52, condition=Op.EQ)
            + Op.JUMPDEST
            + Op.POP
            + Op.MLOAD(offset=0x0)
            + Op.SSTORE(key=0x1, value=Op.DUP1)
            + Op.JUMPI(pc=0x43, condition=Op.GT(Op.DUP2, 0x0))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
            + Op.SWAP5
            + Op.SUB(Op.GAS, 0x3E8)
            + Op.CALL
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x20]
            + Op.DUP2
            + Op.DUP1
            + Op.DUP3
            + Op.SWAP5
            + Op.SUB(Op.GAS, 0x3E8)
            + Op.POP(Op.CALL)
            + Op.DUP1
            + Op.JUMP(pc=0x32)
            + Op.JUMPDEST
            + Op.POP(
                Op.CALLCODE(
                    gas=Op.SUB(Op.GAS, 0x3E8),
                    address=Op.DUP8,
                    value=Op.DUP1,
                    args_offset=Op.DUP2,
                    args_size=Op.DUP2,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.JUMP(pc=0x2D)
            + Op.JUMPDEST
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.SUB(Op.GAS, 0x3E8),
                    address=Op.DUP7,
                    args_offset=Op.DUP2,
                    args_size=Op.DUP2,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.JUMP(pc=0x25)
            + Op.JUMPDEST
            + Op.PUSH5[0x60016000F3]
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.DUP2
            + Op.MSTORE
            + Op.CREATE(value=Op.DUP3, offset=0x1B, size=0x5)
            + Op.JUMPI(pc=0xAA, condition=Op.GT)
            + Op.JUMPDEST
            + Op.POP
            + Op.SLOAD(key=0xFFFF)
            + Op.JUMP(pc=0x12)
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.SSTORE(key=0xFFFF, value=Op.ADD)
            + Op.CODESIZE
            + Op.JUMP(pc=0xA1)
        ),
        storage={0xFFFF: 0xFFFFFFFFFFFFFFFE},
        nonce=18446744073709551614,
        address=Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x0)
            + Op.SLOAD(key=0xFFFF)
            + Op.MSTORE(offset=0x0, value=0x6005600C60003960056000F36001600155)
            + Op.PUSH1[0x0]
            + Op.SWAP2
            + Op.JUMPI(pc=0x5E, condition=Op.EQ(Op.DUP2, 0x0))
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.JUMPI(pc=0x4F, condition=Op.EQ)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x2, value=Op.DUP2)
            + Op.JUMPI(pc=0x43, condition=Op.GT(Op.DUP3, 0x0))
            + Op.JUMPDEST
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.MSTORE
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.SSTORE(key=0xFFFF, value=Op.ADD)
            + Op.CODESIZE
            + Op.JUMP(pc=0x39)
            + Op.JUMPDEST
            + Op.SWAP1
            + Op.POP
            + Op.CREATE2(value=0x0, offset=0xF, size=0x11, salt=Op.DUP1)
            + Op.SWAP1
            + Op.JUMP(pc=0x2D)
            + Op.JUMPDEST
            + Op.SWAP2
            + Op.POP
            + Op.PUSH1[0x1]
            + Op.CREATE(value=0x0, offset=0xF, size=0x11)
            + Op.SWAP3
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x26)
        ),
        storage={0xFFFF: 0xFFFFFFFFFFFFFFFF},
        nonce=18446744073709551615,
        address=Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 14, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x09f07a698496a643301174853c4f7f1eaab166be"): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={
                        1: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        2: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={
                        1: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        2: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x09f07a698496a643301174853c4f7f1eaab166be"): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={
                        1: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        2: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={
                        1: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        2: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 16, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x1cfc908bb573719841cad6a8bc34e7c1ce5ee020"): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                callee: Account(
                    storage={
                        2: 0x1CFC908BB573719841CAD6A8BC34E7C1CE5EE020,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={
                        1: 0x1CFC908BB573719841CAD6A8BC34E7C1CE5EE020,
                        65535: 0xFFFFFFFFFFFFFFFE,
                    },
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x99f1bfb202fdf527e07fb8eb682a03c713aeaf11"): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                callee: Account(
                    storage={
                        2: 0x99F1BFB202FDF527E07FB8EB682A03C713AEAF11,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={
                        1: 0x99F1BFB202FDF527E07FB8EB682A03C713AEAF11,
                        65535: 0xFFFFFFFFFFFFFFFE,
                    },
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 17, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x09f07a698496a643301174853c4f7f1eaab166be"): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={
                        1: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        2: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={
                        1: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        2: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x09f07a698496a643301174853c4f7f1eaab166be"): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={
                        1: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        2: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={
                        1: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        2: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 20, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    code=bytes.fromhex("00")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    code=bytes.fromhex("00")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 21, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    code=bytes.fromhex("00")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    code=bytes.fromhex("00")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 22, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x1cfc908bb573719841cad6a8bc34e7c1ce5ee020"): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    code=bytes.fromhex("00")
                ),
                callee: Account(
                    storage={
                        2: 0x1CFC908BB573719841CAD6A8BC34E7C1CE5EE020,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={
                        1: 0x1CFC908BB573719841CAD6A8BC34E7C1CE5EE020,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    code=bytes.fromhex("00")
                ),
                Address("0x99f1bfb202fdf527e07fb8eb682a03c713aeaf11"): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                callee: Account(
                    storage={
                        2: 0x99F1BFB202FDF527E07FB8EB682A03C713AEAF11,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={
                        1: 0x99F1BFB202FDF527E07FB8EB682A03C713AEAF11,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 23, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    code=bytes.fromhex("00")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    code=bytes.fromhex("00")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 18, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    code=bytes.fromhex("00")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    code=bytes.fromhex("00")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 19, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    code=bytes.fromhex("00")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    code=bytes.fromhex("00")
                ),
                callee: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "600435602435906044359060643561ffff545b848110608b575060005260029080156079575b600181146066575b146052575b506000518060015560008111604357005b600080808080946103e85a03f1005b60006020818082946103e85a03f150806032565b60206000818180876103e85a03f250602d565b602060008181866103e85a03f4506025565b6460016000f360009081526005601b82f01160aa575b5061ffff546012565b60010161ffff553860a156"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    code=bytes.fromhex(
                        "60003561ffff54706005600c60003960056000f3600160015560005260009160008114605e575b600114604f575b81600255600082116043575b5060005260206000f35b60010161ffff55386039565b9050806011600f6000f590602d565b915060016011600f6000f0929050602656"  # noqa: E501
                    ),
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
