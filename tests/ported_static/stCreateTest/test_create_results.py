"""
Verify the value CREATE/CREATE2 leaves on the stack, the returndata, and
the deployed code for each constructor outcome — success, OOG, empty
revert, revert with data, empty deploy, and in-init SELFDESTRUCT — plus
each CALL-kind's result when calling the successfully created contract,
and the frame-aborting RETURNDATACOPY past an empty return buffer.

Written by Ori Pomerantz (qbzzt1@gmail.com).

Ported from:
state_tests/stCreateTest/CreateResultsFiller.yml

@manually-enhanced: Do not overwrite. The ported PUSH2 0xFFFF sub-call
budgets are replaced by length-preserving forward-all-gas sequences (the
fixed budget starves EIP-8037 state gas), the created accounts are now
asserted per case (code, nonce, or non-existence), and the per-case
posts are an explicit switch over the decoded calldata triple.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Fork,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create2_address,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# The dispatcher's LLL-derived bytecode hardcodes every jump target and
# code-copy offset, so all edits below preserve instruction lengths.
CONTRACT_1_ADDRESS = 0x60A7
CREATE2_SALT = 0x5A17
# PC values the dispatcher snapshots right after the create (slot 0x20)
# and after the call section (slot 0x21); fixed by the code layout.
CREATE_PC = 295
CALL_PC = 551
# Below the SHA3-OOG constructor's memory-expansion cost (which must
# fail) and above Amsterdam's state-gas needs (which must not).
TX_GAS = 9_437_184

# Calldata triples (creation kind, call kind, constructor kind) in the
# ported data order. creation: 1=CREATE, 2=CREATE2. call: 0=none,
# 1=CALL, 2=CALLCODE, 3=DELEGATECALL, 4=STATICCALL. constructor:
# 0/4=success, 1=OOG, 2=revert, 3=revert-with-data, 5=empty deploy,
# 6=SELFDESTRUCT in init (4 also RETURNDATACOPYs past the empty
# return buffer, aborting the whole dispatcher frame).
CASES: list[tuple[int, int, int]] = [
    (1, 1, 0),
    (1, 2, 0),
    (1, 3, 0),
    (1, 4, 0),
    (2, 1, 0),
    (2, 2, 0),
    (2, 3, 0),
    (2, 4, 0),
    (1, 0, 1),
    (2, 0, 1),
    (1, 0, 2),
    (2, 0, 2),
    (1, 0, 5),
    (2, 0, 5),
    (1, 0, 6),
    (2, 0, 6),
    (1, 0, 3),
    (2, 0, 3),
    (1, 1, 4),
    (1, 2, 4),
    (1, 3, 4),
    (1, 4, 4),
    (2, 1, 4),
    (2, 2, 4),
    (2, 3, 4),
    (2, 4, 4),
]

# Constructor fragment (offset, size) within the dispatcher's code:
# the dispatcher CODECOPYs these windows as the init code it creates
# from, keyed by the constructor kind.
FRAGMENTS: dict[int, tuple[int, int]] = {
    0: (0x250, 0x21),
    1: (0x271, 0x29),
    2: (0x29A, 0x26),
    3: (0x2C0, 0x2C),
    4: (0x250, 0x21),
    5: (0x2EC, 0x28),
    6: (0x314, 0x2A),
}


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateResultsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("d", range(len(CASES)), ids=lambda d: f"d{d}")
@pytest.mark.pre_alloc_mutable
def test_create_results(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
) -> None:
    """Verify create results and follow-up calls per constructor kind."""
    creation, call_kind, constructor = CASES[d]
    contract_1 = Address(CONTRACT_1_ADDRESS)
    sender = pre.fund_eoa()

    # Length-preserving stand-in for the ported PUSH2 0xFFFF gas
    # operand: two JUMPDESTs pad the 3-byte slot so every hardcoded
    # jump target and code-copy offset stays valid, while GAS forwards
    # everything (a fixed budget starves EIP-8037 state gas).
    forward_all_gas = Op.JUMPDEST + Op.JUMPDEST + Op.GAS

    # The 18-byte contract each successful constructor deploys: call
    # contract_1 (as a 2-byte push, part of the fixed layout) and stop.
    contract_code = (
        Op.CALL(
            gas=forward_all_gas,
            address=CONTRACT_1_ADDRESS,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP
    )

    # Source: lll
    # {
    #   ; Variables are 0x20 bytes (= 256 bits) apart, except for
    #   ; code buffers that get 0x100 (256 bytes)
    #   (def 'creation          0x100)
    #   (def 'callType          0x120)
    #   (def 'constructor       0x140)
    #   (def 'contractCode      0x200)
    #   (def 'constructorCode   0x300)
    #   (def 'extCode           0x400)
    #   (def 'contractLength    0x520)
    #   (def 'constructorLength 0x540)
    #   (def 'extLength         0x560)
    #   (def 'addr1             0x600)
    #   (def 'addr2             0x620)
    #   (def 'callRet           0x640)
    #   (def 'retData0          0x160)   ; storage for returned data
    #   ; Other constants
    #   (def 'NOP 0)   ; No OPeration
    #   ; Understand the input.
    #   [creation]       $0x04
    #   [callType]       $0x24
    #   [constructor]    $0x44
    #   ; The contract code
    #   (def 'contractMacro
    #             (lll
    #                (call 0xFFFF 0x60A7 0 0 0 0 0)
    #                contractCode
    #             ) ; inner lll
    #   )
    #   ; I did not want to rely on knowing the address at which the contract
    # ... (138 more lines)
    dispatcher_code = (
        Op.MSTORE(offset=0x100, value=Op.CALLDATALOAD(offset=0x4))
        + Op.MSTORE(offset=0x120, value=Op.CALLDATALOAD(offset=0x24))
        + Op.MSTORE(offset=0x140, value=Op.CALLDATALOAD(offset=0x44))
        + Op.JUMPI(
            pc=Op.PUSH2[0x2F],
            condition=Op.OR(
                Op.EQ(Op.MLOAD(offset=0x140), 0x0),
                Op.EQ(Op.MLOAD(offset=0x140), 0x4),
            ),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x3E])
        + Op.JUMPDEST
        + Op.PUSH1[0x21]
        + Op.CODECOPY(dest_offset=0x300, offset=0x250, size=Op.DUP1)
        + Op.PUSH2[0x540]
        + Op.MSTORE
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x51], condition=Op.EQ(Op.MLOAD(offset=0x140), 0x1)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x60])
        + Op.JUMPDEST
        + Op.PUSH1[0x29]
        + Op.CODECOPY(dest_offset=0x300, offset=0x271, size=Op.DUP1)
        + Op.PUSH2[0x540]
        + Op.MSTORE
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x73], condition=Op.EQ(Op.MLOAD(offset=0x140), 0x2)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x82])
        + Op.JUMPDEST
        + Op.PUSH1[0x26]
        + Op.CODECOPY(dest_offset=0x300, offset=0x29A, size=Op.DUP1)
        + Op.PUSH2[0x540]
        + Op.MSTORE
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x95], condition=Op.EQ(Op.MLOAD(offset=0x140), 0x3)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xA4])
        + Op.JUMPDEST
        + Op.PUSH1[0x2C]
        + Op.CODECOPY(dest_offset=0x300, offset=0x2C0, size=Op.DUP1)
        + Op.PUSH2[0x540]
        + Op.MSTORE
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xB7], condition=Op.EQ(Op.MLOAD(offset=0x140), 0x5)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xC6])
        + Op.JUMPDEST
        + Op.PUSH1[0x28]
        + Op.CODECOPY(dest_offset=0x300, offset=0x2EC, size=Op.DUP1)
        + Op.PUSH2[0x540]
        + Op.MSTORE
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xD9], condition=Op.EQ(Op.MLOAD(offset=0x140), 0x6)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xE8])
        + Op.JUMPDEST
        + Op.PUSH1[0x2A]
        + Op.CODECOPY(dest_offset=0x300, offset=0x314, size=Op.DUP1)
        + Op.PUSH2[0x540]
        + Op.MSTORE
        + Op.JUMPDEST
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x200, offset=0x33E, size=Op.DUP1)
        + Op.PUSH2[0x520]
        + Op.MSTORE
        + Op.JUMPI(pc=0x117, condition=Op.EQ(Op.MLOAD(offset=0x100), 0x1))
        + Op.MSTORE(
            offset=0x600,
            value=Op.CREATE2(
                value=0x0,
                offset=0x300,
                size=Op.MLOAD(offset=0x540),
                salt=0x5A17,
            ),
        )
        + Op.JUMP(pc=0x126)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x600,
            value=Op.CREATE(
                value=0x0, offset=0x300, size=Op.MLOAD(offset=0x540)
            ),
        )
        + Op.JUMPDEST
        + Op.SSTORE(key=0x20, value=Op.PC)
        + Op.SSTORE(key=0x10, value=Op.RETURNDATASIZE)
        + Op.JUMPI(
            pc=0x143,
            condition=Op.OR(
                Op.RETURNDATASIZE, Op.EQ(Op.MLOAD(offset=0x140), 0x4)
            ),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x153)
        + Op.JUMPDEST
        + Op.RETURNDATACOPY(dest_offset=0x160, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x11, value=Op.MLOAD(offset=0x160))
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x560, value=Op.EXTCODESIZE(address=Op.MLOAD(offset=0x600))
        )
        + Op.EXTCODECOPY(
            address=Op.MLOAD(offset=0x600),
            dest_offset=0x400,
            offset=0x0,
            size=Op.MLOAD(offset=0x560),
        )
        + Op.SSTORE(
            key=0x12,
            value=Op.SUB(Op.MLOAD(offset=0x520), Op.MLOAD(offset=0x560)),
        )
        + Op.SSTORE(
            key=0x13,
            value=Op.SUB(Op.MLOAD(offset=0x200), Op.MLOAD(offset=0x400)),
        )
        + Op.JUMPI(pc=0x195, condition=Op.EQ(Op.MLOAD(offset=0x120), 0x1))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1AC)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x640,
            value=Op.CALL(
                gas=forward_all_gas,
                address=Op.MLOAD(offset=0x600),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x1BF, condition=Op.EQ(Op.MLOAD(offset=0x120), 0x2))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1D6)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x640,
            value=Op.CALLCODE(
                gas=forward_all_gas,
                address=Op.MLOAD(offset=0x600),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x1E9, condition=Op.EQ(Op.MLOAD(offset=0x120), 0x3))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1FE)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x640,
            value=Op.DELEGATECALL(
                gas=forward_all_gas,
                address=Op.MLOAD(offset=0x600),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x211, condition=Op.EQ(Op.MLOAD(offset=0x120), 0x4))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x226)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x640,
            value=Op.STATICCALL(
                gas=forward_all_gas,
                address=Op.MLOAD(offset=0x600),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPDEST
        + Op.SSTORE(key=0x21, value=Op.PC)
        + Op.JUMPI(
            pc=0x23E, condition=Op.ISZERO(Op.EQ(Op.MLOAD(offset=0x120), 0x0))
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x24D)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x14, value=Op.SUB(Op.MLOAD(offset=0x640), 0x1))
        + Op.SSTORE(key=0x15, value=Op.RETURNDATASIZE)
        + Op.JUMPDEST
        + Op.STOP
        + Op.INVALID
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x200, offset=0xF, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + contract_code
        + Op.POP(Op.SHA3(offset=0x0, size=0x2FFFFF))
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x200, offset=0x17, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + contract_code
        + Op.REVERT(offset=0x0, size=0x0)
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x200, offset=0x14, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + contract_code
        + Op.MSTORE(offset=0x0, value=0x60A7)
        + Op.REVERT(offset=0x0, size=0x20)
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x200, offset=0x1A, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + contract_code
        + Op.MSTORE(offset=0x0, value=0x60A7)
        + Op.STOP
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x200, offset=0x16, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + contract_code
        + Op.MSTORE(offset=0x0, value=0x60A7)
        + Op.SELFDESTRUCT(address=0x0)
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x200, offset=0x18, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + contract_code
        + contract_code
    )

    # Guard the hardcoded layout the bytecode's jump targets and the
    # FRAGMENTS table rely on.
    dispatcher_bytes = bytes(dispatcher_code)
    assert len(dispatcher_bytes) == 0x350, "dispatcher layout drifted"
    assert dispatcher_bytes[0x33E:0x350] == bytes(contract_code), (
        "reference contract code slot drifted"
    )
    # The SHA3-OOG constructor must stay unaffordable.
    assert TX_GAS < fork.memory_expansion_gas_calculator()(
        new_bytes=0x2FFFFF
    ), "budget must not afford the SHA3-OOG constructor"

    # Slots 16-33 hold non-zero sentinels so every overwrite (even with
    # zero) is observable.
    contract_0 = pre.deploy_contract(
        code=dispatcher_code,
        storage={
            16: contract_1,
            18: contract_1,
            19: contract_1,
            20: contract_1,
            21: contract_1,
            32: contract_1,
            33: contract_1,
        },
    )
    # Source: lll
    # {
    #   [[0]] 0x60A7
    # }   ; end of LLL code
    pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=CONTRACT_1_ADDRESS) + Op.STOP,
        address=contract_1,
    )

    # Decode the case into the created account's address and the
    # expected post-state.
    if creation == 1:
        created = compute_create_address(address=contract_0, nonce=1)
    else:
        frag_offset, frag_size = FRAGMENTS[constructor]
        created = compute_create2_address(
            contract_0,
            CREATE2_SALT,
            dispatcher_bytes[frag_offset : frag_offset + frag_size],
        )

    # The word the dispatcher stores when comparing its reference copy
    # of the contract code against a non-existent account's ext code.
    contract_code_word = int.from_bytes(
        bytes(contract_code).ljust(32, b"\x00"), "big"
    )

    post: dict = {}
    if constructor == 4:
        # The create succeeds with an empty return buffer, so the
        # forced RETURNDATACOPY of 32 bytes aborts the whole dispatcher
        # frame: every sentinel survives and nothing was created.
        post[contract_0] = Account(
            storage={
                16: contract_1,
                18: contract_1,
                19: contract_1,
                20: contract_1,
                21: contract_1,
                32: contract_1,
                33: contract_1,
            },
        )
        post[contract_1] = Account(storage={})
        post[created] = Account.NONEXISTENT
    elif constructor == 0:
        # Successful creation and a follow-up call to the new contract,
        # which calls contract_1. Every sentinel is overwritten (the
        # zero results are observable), and only the non-static call
        # kinds let contract_1 store its own address.
        post[contract_0] = Account(
            storage={32: CREATE_PC, 33: CALL_PC},
        )
        post[contract_1] = Account(
            storage={} if call_kind == 4 else {0: contract_1},
        )
        post[created] = Account(code=bytes(contract_code), nonce=1, storage={})
    else:
        # No follow-up call: slots 20/21 keep their sentinels, and the
        # dispatcher records the code/length differences against the
        # created (or never-created) account's empty ext code.
        storage = {
            18: len(bytes(contract_code)),
            19: contract_code_word,
            20: contract_1,
            21: contract_1,
            32: CREATE_PC,
            33: CALL_PC,
        }
        if constructor == 3:
            # The constructor reverted 32 bytes holding contract_1's
            # address; the dispatcher copied them out.
            storage[16] = 32
            storage[17] = contract_1
        post[contract_0] = Account(storage=storage)
        post[contract_1] = Account(storage={})
        if constructor == 5:
            # Empty deploy: the account exists with no code.
            post[created] = Account(code=b"", nonce=1, storage={})
        else:
            # OOG (1), reverts (2, 3), and an in-init SELFDESTRUCT (6,
            # destroyed in its creation transaction per EIP-6780).
            post[created] = Account.NONEXISTENT

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes("048071d3")
        + Hash(creation)
        + Hash(call_kind)
        + Hash(constructor),
        gas_limit=TX_GAS,
    )

    state_test(pre=pre, post=post, tx=tx)
