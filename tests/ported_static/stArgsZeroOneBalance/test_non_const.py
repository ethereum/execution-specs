"""
Test opcodes whose operands are all the contract's own balance.

The balance equals the transaction value, so every operand is 0 or 1.

Ported from:
state_tests/stArgsZeroOneBalance/addNonConstFiller.yml
state_tests/stArgsZeroOneBalance/addmodNonConstFiller.yml
state_tests/stArgsZeroOneBalance/andNonConstFiller.yml
state_tests/stArgsZeroOneBalance/balanceNonConstFiller.yml
state_tests/stArgsZeroOneBalance/byteNonConstFiller.yml
state_tests/stArgsZeroOneBalance/callNonConstFiller.yml
state_tests/stArgsZeroOneBalance/callcodeNonConstFiller.yml
state_tests/stArgsZeroOneBalance/calldatacopyNonConstFiller.yml
state_tests/stArgsZeroOneBalance/calldataloadNonConstFiller.yml
state_tests/stArgsZeroOneBalance/codecopyNonConstFiller.yml
state_tests/stArgsZeroOneBalance/createNonConstFiller.yml
state_tests/stArgsZeroOneBalance/delegatecallNonConstFiller.yml
state_tests/stArgsZeroOneBalance/divNonConstFiller.yml
state_tests/stArgsZeroOneBalance/eqNonConstFiller.yml
state_tests/stArgsZeroOneBalance/expNonConstFiller.yml
state_tests/stArgsZeroOneBalance/extcodecopyNonConstFiller.yml
state_tests/stArgsZeroOneBalance/extcodesizeNonConstFiller.yml
state_tests/stArgsZeroOneBalance/gtNonConstFiller.yml
state_tests/stArgsZeroOneBalance/iszeroNonConstFiller.yml
state_tests/stArgsZeroOneBalance/jumpNonConstFiller.yml
state_tests/stArgsZeroOneBalance/jumpiNonConstFiller.yml
state_tests/stArgsZeroOneBalance/log0NonConstFiller.yml
state_tests/stArgsZeroOneBalance/log1NonConstFiller.yml
state_tests/stArgsZeroOneBalance/log2NonConstFiller.yml
state_tests/stArgsZeroOneBalance/log3NonConstFiller.yml
state_tests/stArgsZeroOneBalance/ltNonConstFiller.yml
state_tests/stArgsZeroOneBalance/mloadNonConstFiller.yml
state_tests/stArgsZeroOneBalance/modNonConstFiller.yml
state_tests/stArgsZeroOneBalance/mstore8NonConstFiller.yml
state_tests/stArgsZeroOneBalance/mstoreNonConstFiller.yml
state_tests/stArgsZeroOneBalance/mulNonConstFiller.yml
state_tests/stArgsZeroOneBalance/mulmodNonConstFiller.yml
state_tests/stArgsZeroOneBalance/notNonConstFiller.yml
state_tests/stArgsZeroOneBalance/orNonConstFiller.yml
state_tests/stArgsZeroOneBalance/returnNonConstFiller.yml
state_tests/stArgsZeroOneBalance/sdivNonConstFiller.yml
state_tests/stArgsZeroOneBalance/sgtNonConstFiller.yml
state_tests/stArgsZeroOneBalance/sha3NonConstFiller.yml
state_tests/stArgsZeroOneBalance/signextNonConstFiller.yml
state_tests/stArgsZeroOneBalance/sloadNonConstFiller.yml
state_tests/stArgsZeroOneBalance/sltNonConstFiller.yml
state_tests/stArgsZeroOneBalance/smodNonConstFiller.yml
state_tests/stArgsZeroOneBalance/sstoreNonConstFiller.yml
state_tests/stArgsZeroOneBalance/subNonConstFiller.yml
state_tests/stArgsZeroOneBalance/suicideNonConstFiller.yml
state_tests/stArgsZeroOneBalance/xorNonConstFiller.yml
"""

from typing import Callable, Dict, Tuple

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
    keccak256,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CANARY_SLOT = 0x100
CANARY = 0xC0DE
WORD_MASK = 2**256 - 1
CALLDATA = Bytes("11223344")

# Opcodes whose result is stored in slot 0, with the expected results for
# operand values 0 and 1.
STORED_RESULT: Dict[
    str, Tuple[Callable[[Bytecode], Bytecode], Tuple[int, ...]]
] = {
    "add": (lambda x: Op.ADD(x, x), (0, 2)),
    "addmod": (lambda x: Op.ADDMOD(x, x, x), (0, 0)),
    "and": (lambda x: Op.AND(x, x), (0, 1)),
    "balance": (lambda x: Op.BALANCE(x), (0, 0)),
    "byte": (lambda x: Op.BYTE(x, x), (0, 0)),
    "call": (
        lambda x: Op.CALL(x, x, x, x, x, x, x),
        (1, 0),
    ),
    "callcode": (
        lambda x: Op.CALLCODE(x, x, x, x, x, x, x),
        (1, 0),
    ),
    "calldataload": (lambda x: Op.CALLDATALOAD(x), (0, 0)),
    "calldataload_with_data": (
        lambda x: Op.CALLDATALOAD(x),
        tuple(
            int.from_bytes(CALLDATA[v:].ljust(32, b"\0"), "big")
            for v in (0, 1)
        ),
    ),
    "delegatecall": (
        lambda x: Op.DELEGATECALL(x, x, x, x, x, x),
        (1, 0),
    ),
    "div": (lambda x: Op.DIV(x, x), (0, 1)),
    "eq": (lambda x: Op.EQ(x, x), (1, 1)),
    "exp": (lambda x: Op.EXP(x, x), (1, 1)),
    "extcodesize": (lambda x: Op.EXTCODESIZE(x), (0, 0)),
    "gt": (lambda x: Op.GT(x, x), (0, 0)),
    "iszero": (lambda x: Op.ISZERO(x), (1, 0)),
    "lt": (lambda x: Op.LT(x, x), (0, 0)),
    "mload": (lambda x: Op.MLOAD(x), (0, 0)),
    "mod": (lambda x: Op.MOD(x, x), (0, 0)),
    "mul": (lambda x: Op.MUL(x, x), (0, 1)),
    "mulmod": (lambda x: Op.MULMOD(x, x, x), (0, 0)),
    "not": (lambda x: Op.NOT(x), (WORD_MASK, WORD_MASK - 1)),
    "or": (lambda x: Op.OR(x, x), (0, 1)),
    "sdiv": (lambda x: Op.SDIV(x, x), (0, 1)),
    "sgt": (lambda x: Op.SGT(x, x), (0, 0)),
    "sha3": (
        lambda x: Op.SHA3(x, x),
        tuple(int.from_bytes(keccak256(bytes(v)), "big") for v in (0, 1)),
    ),
    "signext": (lambda x: Op.SIGNEXTEND(x, x), (0, 1)),
    "slt": (lambda x: Op.SLT(x, x), (0, 0)),
    "smod": (lambda x: Op.SMOD(x, x), (0, 0)),
    "sub": (lambda x: Op.SUB(x, x), (0, 0)),
    "xor": (lambda x: Op.XOR(x, x), (0, 0)),
}

# Opcodes that complete without producing a stored result.
NO_RESULT: Dict[str, Callable[[Bytecode], Bytecode]] = {
    "calldatacopy": lambda x: Op.CALLDATACOPY(x, x, x),
    "codecopy": lambda x: Op.CODECOPY(x, x, x),
    "extcodecopy": lambda x: Op.EXTCODECOPY(x, x, x, x),
    "log0": lambda x: Op.LOG0(x, x),
    "log1": lambda x: Op.LOG1(x, x, x),
    "log2": lambda x: Op.LOG2(x, x, x, x),
    "log3": lambda x: Op.LOG3(x, x, x, x, x),
    "mstore": lambda x: Op.MSTORE(x, x),
    "mstore8": lambda x: Op.MSTORE8(x, x),
    "return": lambda x: Op.RETURN(x, x),
}


@pytest.mark.ported_from(
    [
        "state_tests/stArgsZeroOneBalance/addNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/addmodNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/andNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/balanceNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/byteNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/callNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/callcodeNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/calldatacopyNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/calldataloadNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/codecopyNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/createNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/delegatecallNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/divNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/eqNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/expNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/extcodecopyNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/extcodesizeNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/gtNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/iszeroNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/jumpNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/jumpiNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/log0NonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/log1NonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/log2NonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/log3NonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/ltNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/mloadNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/modNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/mstore8NonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/mstoreNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/mulNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/mulmodNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/notNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/orNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/returnNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/sdivNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/sgtNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/sha3NonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/signextNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/sloadNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/sltNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/smodNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/sstoreNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/subNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/suicideNonConstFiller.yml",
        "state_tests/stArgsZeroOneBalance/xorNonConstFiller.yml",
    ],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize("tx_value", [0, 1])
@pytest.mark.parametrize(
    "opcode",
    [
        *[
            pytest.param(
                name,
                marks=pytest.mark.valid_from("Homestead")
                if name == "delegatecall"
                else (),
            )
            for name in STORED_RESULT
        ],
        *NO_RESULT,
        "jump",
        "jumpi",
        "sload",
        "sstore",
        pytest.param("create", marks=pytest.mark.valid_from("SpuriousDragon")),
        pytest.param("suicide", marks=pytest.mark.valid_from("Cancun")),
    ],
)
def test_non_const(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: str,
    tx_value: int,
) -> None:
    """Run an opcode with balance operands after storing a canary."""
    sender = pre.fund_eoa()
    operand = Op.BALANCE(Op.ADDRESS)
    tx_data = CALLDATA if opcode == "calldataload_with_data" else Bytes()

    storage: Dict[int, int] = {CANARY_SLOT: CANARY}
    if opcode in STORED_RESULT:
        expression, result = STORED_RESULT[opcode]
        body = Op.SSTORE(key=0, value=expression(operand))
        storage[0] = result[tx_value]
    elif opcode in NO_RESULT:
        body = NO_RESULT[opcode](operand)
    elif opcode == "jump":
        body = Op.JUMP(operand)
        storage = {}
    elif opcode == "jumpi":
        body = Op.JUMPI(operand, operand)
        if tx_value:
            storage = {}
    elif opcode == "sload":
        body = Op.SSTORE(key=3, value=Op.SLOAD(operand))
        storage[3] = 0
    elif opcode == "sstore":
        body = Op.SSTORE(key=operand, value=operand)
        storage[tx_value] = tx_value
    elif opcode == "create":
        body = Op.SSTORE(key=0, value=Op.CREATE(operand, operand, operand))
    elif opcode == "suicide":
        body = Op.SELFDESTRUCT(operand)
    else:
        raise ValueError(f"Unknown opcode case: {opcode}")

    target = pre.deploy_contract(
        code=Op.SSTORE(key=CANARY_SLOT, value=CANARY) + body + Op.STOP,
    )

    post: Dict[Address, Account] = {}
    if opcode == "create":
        created = compute_create_address(address=target, nonce=1)
        storage[0] = int.from_bytes(created, "big")
        post[created] = Account(nonce=1, balance=tx_value)
    if opcode == "suicide":
        post[target] = Account(storage=storage, balance=0)
    else:
        post[target] = Account(storage=storage)

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data,
        value=tx_value,
        protected=fork.supports_protected_txs(),
    )

    state_test(pre=pre, post=post, tx=tx)
