"""
Delegate calls CREATE/CREATE2 from an account with max allowed nonce.

Contract A raises its nonce to the requested value, then reaches
contract B through DELEGATECALL, CALLCODE or CALL; B runs CREATE or
CREATE2 in whichever context executes it.

Ported from:
state_tests/stCreate2/CREATE2_HighNonceDelegatecallFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

MAX_NONCE = 2**64 - 1
NONCE_SLOT = 0xFFFF
CALL_TYPES = {"DelegateCall": 0, "CallCode": 1, "Call": 2}
CREATE_TYPES = {"Create": 0, "Create2": 1}
# initcode: { codecopy(0, 12, 5); return(0, 5); sstore(1, 1) }
INITCODE = bytes.fromhex("6005600c60003960056000f36001600155")
DEPLOYED_CODE = bytes.fromhex("6001600155")


def created_address(creator: Address, nonce: int, create_type: str) -> Address:
    """Return the address B's code creates from `creator` at `nonce`."""
    if create_type == "Create2":
        return compute_create_address(
            address=creator, salt=nonce, initcode=INITCODE, opcode=Op.CREATE2
        )
    return compute_create_address(address=creator, nonce=nonce)


def nonce_id(nonce: int) -> str:
    """Return the test-id label of a nonce."""
    return "MaxNonce" if nonce == MAX_NONCE else "MaxNonceMinus1"


@pytest.mark.ported_from(
    ["state_tests/stCreate2/CREATE2_HighNonceDelegatecallFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("create_type", list(CREATE_TYPES))
@pytest.mark.parametrize("b_nonce", [MAX_NONCE - 1, MAX_NONCE], ids=nonce_id)
@pytest.mark.parametrize("call_type", list(CALL_TYPES))
@pytest.mark.parametrize("a_nonce", [MAX_NONCE - 1, MAX_NONCE], ids=nonce_id)
def test_create2_high_nonce_delegatecall(
    state_test: StateTestFiller,
    pre: Alloc,
    a_nonce: int,
    call_type: str,
    b_nonce: int,
    create_type: str,
) -> None:
    """Delegate calls CREATE/CREATE2 from an account with max nonce."""
    sender = pre.fund_eoa()

    # Source: yul
    # berlin
    # {
    #   let createtype    := calldataload(0)
    #   let contextnonce  := sload(0xffff)
    #
    #   // initcode: { codecopy(0, 12, 5); return(0, 5); sstore(1, 1) }
    #   mstore(0, 0x6005600c60003960056000f36001600155 )
    #   let addr
    #   if eq(createtype, 0) {
    #     addr := create(0, sub(32, 17), 17)
    #   }
    #   if eq(createtype, 1) {
    #     // We use the context nonce to mimic CREATE's nonce based address calculation and make verification easier  # noqa: E501
    #     addr := create2(0, sub(32, 17), 17, contextnonce)
    #   }
    #   sstore(2, addr)
    #   if gt(addr, 0) { sstore(0xffff, add(contextnonce, 1)) }
    #   mstore(0, addr)
    #   return(0, 32)
    # }
    b_code = (
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
    )
    b_contracts = {
        nonce: pre.deploy_contract(
            code=b_code, storage={NONCE_SLOT: nonce}, nonce=nonce
        )
        for nonce in (MAX_NONCE - 1, MAX_NONCE)
    }
    b = b_contracts[b_nonce]
    # Source: yul
    # berlin
    # {
    #   let calltype      := calldataload(4)
    #   let callernonce   := calldataload(36)
    #   let destnonce     := calldataload(68)
    #   let createtype    := calldataload(100)
    #
    #   for { let contextnonce := sload(0xffff) } lt(contextnonce, callernonce) { contextnonce := sload(0xffff) } {  # noqa: E501
    #     // We have a lower nonce than required for the caller, create dummy contract to increase nonce  # noqa: E501
    #     mstore(0, 0x60016000f3)
    #     let addr := create(0, sub(32, 5), 5)
    #     if gt(addr, 0) { sstore(0xffff, add(contextnonce, 1)) }
    #   }
    #
    #   mstore(0, createtype)
    #   if eq(calltype, 0) {
    #     pop(delegatecall(sub(gas(), 1000), destnonce, 0, 32, 0, 32))
    #   }
    #   if eq(calltype, 1) {
    #     pop(callcode(sub(gas(), 1000), destnonce, 0, 0, 32, 0, 32))
    #   }
    #   if eq(calltype, 2) {
    #     pop(call(sub(gas(), 1000), destnonce, 0, 0, 32, 0, 32))
    #   }
    #   let result := mload(0)
    #   sstore(1, result)
    #   if gt(result, 0) {
    #     pop(call(sub(gas(), 1000), result, 0, 0, 0, 0, 0))
    #   }
    # }
    a = pre.deploy_contract(
        code=Op.CALLDATALOAD(offset=0x4)
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
        + Op.DUP1 * 4
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
            )
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
            )
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
        + Op.JUMP(pc=0xA1),
        storage={NONCE_SLOT: MAX_NONCE - 1},
        nonce=MAX_NONCE - 1,
    )

    tx = Transaction(
        sender=sender,
        to=a,
        data=Bytes("917694f9")
        + Hash(CALL_TYPES[call_type])
        + Hash(a_nonce)
        + Hash(b, left_padding=True)
        + Hash(CREATE_TYPES[create_type]),
    )

    post: dict = {sender: Account(nonce=1)}
    for contract in (a, *b_contracts.values()):
        post[created_address(contract, MAX_NONCE, create_type)] = (
            Account.NONEXISTENT
        )
    if a_nonce == MAX_NONCE:
        post[compute_create_address(address=a, nonce=MAX_NONCE - 1)] = Account(
            code=b"\0", nonce=1
        )
    for nonce, contract in b_contracts.items():
        post[contract] = Account(storage={NONCE_SLOT: nonce}, nonce=nonce)

    if call_type == "Call":
        context, context_nonce = b, b_nonce
    else:
        context, context_nonce = a, a_nonce
    created = Address(0)
    if context_nonce < MAX_NONCE:
        created = created_address(context, context_nonce, create_type)
        post[created] = Account(storage={1: 1}, code=DEPLOYED_CODE)
    context_storage: dict[int, Address | int] = {
        2: created,
        NONCE_SLOT: MAX_NONCE,
    }
    if context == a:
        context_storage[1] = created
    else:
        post[a] = Account(
            storage={1: created, NONCE_SLOT: a_nonce}, nonce=a_nonce
        )
    post[context] = Account(storage=context_storage, nonce=MAX_NONCE)

    state_test(pre=pre, post=post, tx=tx)
