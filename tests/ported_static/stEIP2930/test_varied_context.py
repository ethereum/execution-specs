"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP2930/variedContextFiller.yml

@manually-enhanced: Do not overwrite. This test measures gas
consumption around SSTORE/CALL/SELFDESTRUCT in various access-list
contexts via `Op.GAS`. EIP-8037/8038 reprice several components;
with an empty reservoir (the case here) the state-gas portion
spills back into regular gas, so each measurement shifts by its
`(Amsterdam - Cancun)` delta. Every delta below is derived from the
fork's own opcode gas model, so it is exactly 0 pre-EIP-8037 and
tracks parameter changes: warm/cold fresh SSTORE-sets, the
NEW_ACCOUNT spill for CALL-with-value and SELFDESTRUCT-to-non-alive
(the latter also gaining `ACCOUNT_WRITE` and the cold reprice), and
the cold account/storage access reprices. The `*ValidGas`
parametrizations instead forward a fixed in-bytecode gas budget that
EIP-8038 made insufficient; those budgets are bumped by the inner
SSTORE-write increase so the success path stays funded while the
under-funded cold path still runs out of gas.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytes,
    Conditional,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create2_address,
    compute_create_address,
)
from execution_testing.forks import Cancun, Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CREATE2_SALT = 0x5A17


@pytest.mark.ported_from(
    ["state_tests/stEIP2930/variedContextFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.execute(
    pytest.mark.skip(reason="Expects address zero to be empty")
)
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="delegateCallerInAccessList",
        ),
        pytest.param(
            1,
            0,
            0,
            id="delegateCalleeInAccessList",
        ),
        pytest.param(
            2,
            0,
            0,
            id="callcodeCallerInAccessList",
        ),
        pytest.param(
            3,
            0,
            0,
            id="callcodeCalleeInAccessList",
        ),
        pytest.param(
            4,
            0,
            0,
            id="callCallerInAccessList",
        ),
        pytest.param(
            5,
            0,
            0,
            id="callCalleeInAccessList",
        ),
        pytest.param(
            6,
            0,
            0,
            id="staticcallCallerInAccessList",
        ),
        pytest.param(
            7,
            0,
            0,
            id="staticcallCalleeInAccessList",
        ),
        pytest.param(
            8,
            0,
            0,
            id="callRevertCalleeInAccessList",
        ),
        pytest.param(
            9,
            0,
            0,
            id="callRevertCallerInAccessList",
        ),
        pytest.param(
            10,
            0,
            0,
            id="callWriteSuicideValid",
        ),
        pytest.param(
            11,
            0,
            0,
            id="callWriteSuicideInvalid",
        ),
        pytest.param(
            12,
            0,
            0,
            id="callReadSuicideValid",
        ),
        pytest.param(
            13,
            0,
            0,
            id="callReadSuicideInvalid",
        ),
        pytest.param(
            14,
            0,
            0,
            id="staticWriteInvalid",
        ),
        pytest.param(
            15,
            0,
            0,
            id="staticWriteValid",
        ),
        pytest.param(
            16,
            0,
            0,
            id="writeValidGas",
        ),
        pytest.param(
            17,
            0,
            0,
            id="writeInvalidOOG",
        ),
        pytest.param(
            18,
            0,
            0,
            id="readValidGas",
        ),
        pytest.param(
            19,
            0,
            0,
            id="readInvalidOOG",
        ),
        pytest.param(
            20,
            0,
            0,
            id="recurseValid",
        ),
        pytest.param(
            21,
            0,
            0,
            id="recurseInvalid",
        ),
        pytest.param(
            22,
            0,
            0,
            id="createValid",
        ),
        pytest.param(
            23,
            0,
            0,
            id="createInvalid",
        ),
        pytest.param(
            24,
            0,
            0,
            id="create2Valid",
        ),
        pytest.param(
            25,
            0,
            0,
            id="create2Invalid",
        ),
        pytest.param(
            26,
            0,
            0,
            id="callCreatedValid",
        ),
        pytest.param(
            27,
            0,
            0,
            id="callCreatedInvalid",
        ),
        pytest.param(
            28,
            0,
            0,
            id="callCreate2edValid",
        ),
        pytest.param(
            29,
            0,
            0,
            id="callCreate2edInvalid",
        ),
        pytest.param(
            30,
            0,
            0,
            id="createAndCallValid",
        ),
        pytest.param(
            31,
            0,
            0,
            id="createAndCallInvalid",
        ),
        pytest.param(
            32,
            0,
            0,
            id="create2AndCallValid",
        ),
        pytest.param(
            33,
            0,
            0,
            id="create2AndCallInvalid",
        ),
        pytest.param(
            34,
            0,
            0,
            id="callTwiceValid",
        ),
        pytest.param(
            35,
            0,
            0,
            id="callTwiceInvalid",
        ),
    ],
)
def test_varied_context(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {
    #    ; 0xC057: DELEGATE_VALID DELEGATE_INVALID
    #    ;         CALL_INVALID CALL_VALID
    #    ;         CALLCODE_VALID CALLCODE_INVALID
    #
    #
    #  ; Write to [[0]], and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #   [[0]]  0x02
    #    [0]   (- @0 (gas) 17)
    #   [[1]] @0
    #
    #  ; The 17 is the cost of the extra opcodes:
    #  ; PUSH1 0x00, MSTORE
    #  ; PUSH1 0x02, PUSH1 0x00, (and then comes the SSTORE we are measuring)
    #  ; GAS
    #
    #  ; Read [[0x60A7]], and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #   [0x20] @@0x60A7
    #    [0]   (- @0 (gas) 16)
    #   [[2]] @0
    #
    #  ; The 16 is the cost of the extra opcodes
    # }
    contract_3 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0x2)
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.MSTORE(offset=0x20, value=Op.SLOAD(key=0x60A7))
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x10),
        )
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={24743: 57005},
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {
    #  ;   STATICCALL_VALID  STATICCALL_INVALID
    #
    #
    #  ; Read [[0x60A7]], and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #  [0x20] @@0x60A7
    #    [0]   (- @0 (gas) 19)
    #  ; The 19 is the cost of the extra opcodes
    #
    #  (return 0x00 0x20) ; a.k.a. @0
    # }
    contract_5 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.MSTORE(offset=0x20, value=Op.SLOAD(key=0x60A7))
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x13),
        )
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.STOP,
        storage={24743: 57005},
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {
    #  ;   CALL_REVERT_VALID     CALL_REVERT_INVALID
    #
    #  ; Write to [[0]], and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #   [[0]]  0x02
    #    [0]   (- @0 (gas) 17)
    #
    #  ; The 17 is the cost of the extra opcodes:
    #  ; PUSH1 0x00, MSTORE
    #  ; PUSH1 0x02, PUSH1 0x00, (and then comes the SSTORE we are measuring)
    #  ; GAS
    #
    #  ; Read [[0x60A7]], and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #   [0x20] (gas)
    #   [0x40] @@0x60A7
    #   [0x20] (- @0x20 (gas) 26)
    #
    #  ; The 29 is the cost of the extra opcodes
    #
    #  ; Send the results the only way we can
    #
    #  (revert 0 0x40)
    # }
    contract_6 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0x2)
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
        )
        + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.MSTORE(offset=0x40, value=Op.SLOAD(key=0x60A7))
        + Op.MSTORE(
            offset=0x20,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x20), Op.GAS), 0x1A),
        )
        + Op.REVERT(offset=0x0, size=0x40)
        + Op.STOP,
        storage={24743: 48879},
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {
    #    ; CALL_WRITE_SUICIDE_VALID      CALL_WRITE_SUICIDE_INVALID
    #    [[0]] 0xDEAD
    #
    #    (selfdestruct 0)
    # }
    contract_8 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0xDEAD)
        + Op.SELFDESTRUCT(address=0x0)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {
    #    ; CALL_READ_SUICIDE_VALID      CALL_READ_SUICIDE_INVALID
    #    @@0
    #
    #    (selfdestruct 0)
    # }
    contract_10 = pre.deploy_contract(
        code=Op.POP(Op.SLOAD(key=0x0))
        + Op.SELFDESTRUCT(address=0x0)
        + Op.STOP,
        storage={0: 0xDEAD0060A7},
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {  ; STATIC_WRITE_VALID     STATIC_WRITE_INVALID
    #    [[0]] 0xDEAD60A7
    #
    #    ; If we get here, GOOD
    #    [0] 0x600D
    #    (return 0 0x20)
    # }
    contract_12 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0xDEAD60A7)
        + Op.MSTORE(offset=0x0, value=0x600D)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {  ; WRITE_INVALID_OOG    WRITE_VALID_NO_OOG
    #
    #   [[0]] 0x600D
    # }
    contract_14 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x600D) + Op.STOP,
        storage={0: 2989},
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {  ; READ_INVALID_OOG    READ_VALID_NO_OOG
    #    [0] @@0x60A7
    #    [[0]] 0x600D
    # }
    contract_16 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.SLOAD(key=0x60A7))
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        storage={0: 2989, 24743: 57005},
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {
    #   ; CREATE_VALID   CREATE_INVALID
    #
    #   ; Variables are 0x20 bytes (= 256 bits) apart, except for
    #   ; code buffers that get 0x100 (256 bytes)
    #   (def 'constructorCode   0x000)
    #   (def 'contractCode      0x100)
    #   (def 'contractLength    0x200)
    #   (def 'constructorLength 0x220)
    #   (def 'addr              0x240)
    #
    #   (def 'bufLength         0x100)
    #
    #   ; Create the contract code
    #   [contractLength]
    #     (lll
    #       {
    #          [[0]] 0xFF
    #       } contractCode
    #     )     ; contract lll
    #
    #   ; Create the constructor code, which runs with the contract address
    #   ; of the newly created contract. If we declare that address in the
    #   ; transaction's access list we get the discount
    #   [constructorLength]
    #     (lll
    #       {
    #          ; write to storage
    #          [0] (gas)
    #          [[0]] 0xFFFF
    # ... (14 more lines)
    contract_18 = pre.deploy_contract(
        code=Op.PUSH1[0x6]
        + Op.CODECOPY(dest_offset=0x100, offset=0x33, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.MSTORE
        + Op.PUSH1[0x21]
        + Op.CODECOPY(dest_offset=0x0, offset=0x39, size=Op.DUP1)
        + Op.PUSH2[0x220]
        + Op.MSTORE
        + Op.MSTORE(
            offset=0x240,
            value=Op.CREATE(
                value=0x0,
                offset=0x0,
                size=Op.ADD(0x100, Op.MLOAD(offset=0x200)),
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x240))
        + Op.STOP
        + Op.INVALID
        + Op.SSTORE(key=0x0, value=0xFF)
        + Op.STOP
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0xFFFF)
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.CODECOPY(dest_offset=0x0, offset=0x100, size=0x100)
        + Op.RETURN(offset=0x0, size=0x10)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #   ; CREATE2_VALID   CREATE2_INVALID
    #
    #   ; Variables are 0x20 bytes (= 256 bits) apart, except for
    #   ; code buffers that get 0x100 (256 bytes)
    #   (def 'constructorCode   0x000)
    #   (def 'contractCode      0x100)
    #   (def 'contractLength    0x200)
    #   (def 'constructorLength 0x220)
    #   (def 'addr              0x240)
    #
    #   (def 'bufLength         0x100)
    #
    #   ; Create the contract code
    #   [contractLength]
    #     (lll
    #       {
    #          [[0]] 0xFF
    #       } contractCode
    #     )     ; contract lll
    #
    #   ; Create the constructor code, which runs with the contract address
    #   ; of the newly created contract. If we declare that address in the
    #   ; transaction's access list we get the discount
    #   [constructorLength]
    #     (lll
    #       {
    #          ; write to storage
    #          [0] (gas)
    #          [[0]] 0xFFFF
    # ... (14 more lines)
    contract_19 = pre.deploy_contract(
        code=Op.PUSH1[0x6]
        + Op.CODECOPY(dest_offset=0x100, offset=0x36, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.MSTORE
        + Op.PUSH1[0x21]
        + Op.CODECOPY(dest_offset=0x0, offset=0x3C, size=Op.DUP1)
        + Op.PUSH2[0x220]
        + Op.MSTORE
        + Op.MSTORE(
            offset=0x240,
            value=Op.CREATE2(
                value=0x0,
                offset=0x0,
                size=Op.ADD(0x100, Op.MLOAD(offset=0x200)),
                salt=CREATE2_SALT,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x240))
        + Op.STOP
        + Op.INVALID
        + Op.SSTORE(key=0x0, value=0xFF)
        + Op.STOP
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0xFFFF)
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.CODECOPY(dest_offset=0x0, offset=0x100, size=0x100)
        + Op.RETURN(offset=0x0, size=0x10)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #   ; CALL_CREATED_VALID     CALL_CREATED_INVALID
    #
    #
    #   ; Variables are 0x20 bytes (= 256 bits) apart, except for
    #   ; code buffers that get 0x100 (256 bytes)
    #   (def 'constructorCode   0x000)
    #   (def 'contractCode      0x100)
    #   (def 'contractLength    0x200)
    #   (def 'constructorLength 0x220)
    #   (def 'addr              0x240)
    #
    #   (def 'bufLength         0x100)
    #
    #   ; Create the contract code
    #   [contractLength]
    #     (lll
    #       {
    #          ; write to storage
    #          [0] (gas)
    #          [[0]] 0xFFFF
    #          [[1]] (- @0 (gas))
    #       } contractCode
    #     )     ; contract lll
    #
    #
    #   ; Create the constructor code
    #   [constructorLength]
    #     (lll
    #       {
    # ... (13 more lines)
    contract_20 = pre.deploy_contract(
        code=Op.PUSH1[0x13]
        + Op.CODECOPY(dest_offset=0x100, offset=0x44, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.MSTORE
        + Op.PUSH1[0xF]
        + Op.CODECOPY(dest_offset=0x0, offset=0x57, size=Op.DUP1)
        + Op.PUSH2[0x220]
        + Op.MSTORE
        + Op.MSTORE(
            offset=0x240,
            value=Op.CREATE(
                value=0x0,
                offset=0x0,
                size=Op.ADD(0x100, Op.MLOAD(offset=0x200)),
            ),
        )
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=Op.MLOAD(offset=0x240),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x240))
        + Op.STOP
        + Op.INVALID
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0xFFFF)
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP
        + Op.CODECOPY(dest_offset=0x0, offset=0x100, size=0x100)
        + Op.RETURN(offset=0x0, size=0x80)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #   ; CALL_CREATE2_ED_VALID     CALL_CREATE2_ED_INVALID
    #
    #
    #   ; Variables are 0x20 bytes (= 256 bits) apart, except for
    #   ; code buffers that get 0x100 (256 bytes)
    #   (def 'constructorCode   0x000)
    #   (def 'contractCode      0x100)
    #   (def 'contractLength    0x200)
    #   (def 'constructorLength 0x220)
    #   (def 'addr              0x240)
    #
    #   (def 'bufLength         0x100)
    #
    #   ; Create the contract code
    #   [contractLength]
    #     (lll
    #       {
    #          ; write to storage
    #          [0] (gas)
    #          [[0]] 0xFFFF
    #          [[1]] (- @0 (gas))
    #       } contractCode
    #     )     ; contract lll
    #
    #
    #   ; Create the constructor code
    #   [constructorLength]
    #     (lll
    #       {
    # ... (13 more lines)
    contract_21 = pre.deploy_contract(
        code=Op.PUSH1[0x13]
        + Op.CODECOPY(dest_offset=0x100, offset=0x47, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.MSTORE
        + Op.PUSH1[0xF]
        + Op.CODECOPY(dest_offset=0x0, offset=0x5A, size=Op.DUP1)
        + Op.PUSH2[0x220]
        + Op.MSTORE
        + Op.MSTORE(
            offset=0x240,
            value=Op.CREATE2(
                value=0x0,
                offset=0x0,
                size=Op.ADD(0x100, Op.MLOAD(offset=0x200)),
                salt=CREATE2_SALT,
            ),
        )
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=Op.MLOAD(offset=0x240),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x240))
        + Op.STOP
        + Op.INVALID
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0xFFFF)
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP
        + Op.CODECOPY(dest_offset=0x0, offset=0x100, size=0x100)
        + Op.RETURN(offset=0x0, size=0x80)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #   ; CREATE_&_CALL_VALID           CREATE_&_CALL_INVALID
    #
    #   ; Variables are 0x20 bytes (= 256 bits) apart, except for
    #   ; code buffers that get 0x100 (256 bytes)
    #   (def 'constructorCode   0x000)
    #   (def 'contractCode      0x100)
    #   (def 'contractLength    0x200)
    #   (def 'constructorLength 0x220)
    #   (def 'addr              0x240)
    #
    #   (def 'bufLength         0x100)
    #
    #   ; Create the contract code
    #   [contractLength]
    #     (lll
    #       {
    #          ; write to storage
    #          [0] (gas)
    #          [[0]] 0xFFFF
    #          [[2]] (- @0 (gas))
    #       } contractCode
    #     )     ; contract lll
    #
    #
    #   ; Create the constructor code
    #   [constructorLength]
    #     (lll
    #       {
    #          ; write to storage
    # ... (18 more lines)
    contract_22 = pre.deploy_contract(
        code=Op.PUSH1[0x13]
        + Op.CODECOPY(dest_offset=0x100, offset=0x44, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.MSTORE
        + Op.PUSH1[0x21]
        + Op.CODECOPY(dest_offset=0x0, offset=0x57, size=Op.DUP1)
        + Op.PUSH2[0x220]
        + Op.MSTORE
        + Op.MSTORE(
            offset=0x240,
            value=Op.CREATE(
                value=0x0,
                offset=0x0,
                size=Op.ADD(0x100, Op.MLOAD(offset=0x200)),
            ),
        )
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=Op.MLOAD(offset=0x240),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x240))
        + Op.STOP
        + Op.INVALID
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0xFFFF)
        + Op.SSTORE(key=0x2, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0xFFFF)
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.CODECOPY(dest_offset=0x0, offset=0x100, size=0x100)
        + Op.RETURN(offset=0x0, size=0x80)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #   ; CREATE2_&_CALL_VALID           CREATE2_&_CALL_INVALID
    #
    #   ; Variables are 0x20 bytes (= 256 bits) apart, except for
    #   ; code buffers that get 0x100 (256 bytes)
    #   (def 'constructorCode   0x000)
    #   (def 'contractCode      0x100)
    #   (def 'contractLength    0x200)
    #   (def 'constructorLength 0x220)
    #   (def 'addr              0x240)
    #
    #   (def 'bufLength         0x100)
    #
    #   ; Create the contract code
    #   [contractLength]
    #     (lll
    #       {
    #          ; write to storage
    #          [0] (gas)
    #          [[0]] 0xFFFF
    #          [[2]] (- @0 (gas))
    #       } contractCode
    #     )     ; contract lll
    #
    #
    #   ; Create the constructor code
    #   [constructorLength]
    #     (lll
    #       {
    #          ; write to storage
    # ... (18 more lines)
    contract_23 = pre.deploy_contract(
        code=Op.PUSH1[0x13]
        + Op.CODECOPY(dest_offset=0x100, offset=0x47, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.MSTORE
        + Op.PUSH1[0x21]
        + Op.CODECOPY(dest_offset=0x0, offset=0x5A, size=Op.DUP1)
        + Op.PUSH2[0x220]
        + Op.MSTORE
        + Op.MSTORE(
            offset=0x240,
            value=Op.CREATE2(
                value=0x0,
                offset=0x0,
                size=Op.ADD(0x100, Op.MLOAD(offset=0x200)),
                salt=CREATE2_SALT,
            ),
        )
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=Op.MLOAD(offset=0x240),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x240))
        + Op.STOP
        + Op.INVALID
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0xFFFF)
        + Op.SSTORE(key=0x2, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0xFFFF)
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.CODECOPY(dest_offset=0x0, offset=0x100, size=0x100)
        + Op.RETURN(offset=0x0, size=0x80)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #   ; CALL_TWICE_VALID     CALL_TWICE_INVALID
    #   [0] (gas)
    #   [[0x00]] 0x60A7
    #   [0] (- @0 (gas))
    #
    #   ; If @@1 is empty, write to it. Otherwise, write to @@2
    #   (if (= @@1 0) {[[1]] @0} {[[2]] @0})
    #
    # }
    contract_25 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x0, value=0x60A7)
        + Op.MSTORE(offset=0x0, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.JUMPI(pc=0x24, condition=Op.EQ(Op.SLOAD(key=0x1), 0x0))
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
        + Op.JUMP(pc=0x2B)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #    ; DELEGATE_VALID   DELEGATE_INVALID
    #
    #    (delegatecall (gas) 0xC057 0 0 0 0)
    # }
    contract_0 = pre.deploy_contract(
        code=Op.DELEGATECALL(
            gas=Op.GAS,
            address=contract_3,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {
    #    ; CALLCODE_VALID       CALLCODE_INVALID
    #    (callcode (gas) 0xC057 0 0 0 0 0)
    # }
    contract_2 = pre.deploy_contract(
        code=Op.CALLCODE(
            gas=Op.GAS,
            address=contract_3,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {
    #    ; CALL_VALID    CALL_INVALID
    #    (call (gas) 0xC057 0 0 0 0 0)
    # }
    contract_1 = pre.deploy_contract(
        code=Op.CALL(
            gas=Op.GAS,
            address=contract_3,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {
    #    ; STATICCALL_VALID  STATICCALL_INVALID
    #
    #    ; Need to store the result here, because static call is, well, static
    #    (staticcall (gas) 0xEAD0C057 0 0 0 0x20)
    #    [[0]] @0
    # }
    contract_4 = pre.deploy_contract(
        code=Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {
    #    ; CALL_WRITE_SUICIDE_VALID      CALL_WRITE_SUICIDE_INVALID
    #    [0] (gas)
    #    (call (gas) 0xDEAD0111 0 0 0 0 0)
    #    [[0]] (- @0 (gas) 0x7fe8)
    # }
    contract_7 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=contract_8,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(
            key=0x0, value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x7FE8)
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {
    #    ; CALL_READ_SUICIDE_VALID      CALL_READ_SUICIDE_INVALID
    #    [0] (gas)
    #    (call (gas) 0xDEAD0112 0 0 0 0 0)
    #    [[0]] (- @0 (gas) 0x7fe8)
    # }
    contract_9 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=contract_10,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(
            key=0x0, value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x7FE8)
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {  ; STATIC_WRITE_VALID     STATIC_WRITE_INVALID
    #
    #    [0x00] 0x0BAD
    #
    #    ; If the call is successful @0 becomes 0x600D
    #    (staticcall (gas) 0xF113 0 0 0 0x20)
    #
    #    [[0]] @0x00
    # }
    contract_11 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xBAD)
        + Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=contract_12,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={0: 24743},
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {  ; WRITE_INVALID_OOG    WRITE_VALID_NO_OOG
    #    (call 0x0B65 0xF114 0 0 0 0 0x20)
    # }
    # EIP-8038 raises the inner SSTORE-write cost. Bump the "valid" gas
    # these callers forward by exactly that increase so their success
    # path stays funded at Amsterdam (preserving the original Cancun
    # margin) while the under-funded cold "invalid" path still OOGs.
    # The contract_13 inner SSTORE is a warm reset; contract_15's is a
    # cold reset. Both bumps are 0 pre-EIP-8037.
    _warm_reset = Op.SSTORE.with_metadata(
        key_warm=True, original_value=1, current_value=1, new_value=2
    )
    _cold_reset = Op.SSTORE.with_metadata(
        key_warm=False, original_value=1, current_value=1, new_value=2
    )
    valid_write_gas = 0xB65 + (
        _warm_reset.gas_cost(fork) - _warm_reset.gas_cost(Cancun)
    )
    valid_read_gas = 0x1800 + (
        _cold_reset.gas_cost(fork) - _cold_reset.gas_cost(Cancun)
    )

    contract_13 = pre.deploy_contract(
        code=Op.CALL(
            gas=valid_write_gas,
            address=contract_14,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {  ; READ_INVALID_OOG    READ_VALID_NO_OOG
    #    (call 0x1800 0xF115 0 0 0 0 0x20)
    # }
    contract_15 = pre.deploy_contract(
        code=Op.CALL(
            gas=valid_read_gas,
            address=contract_16,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {
    #   ; CALL_TWICE_VALID     CALL_TWICE_INVALID
    #   (call (gas) 0xF126 0 0 0 0 0)
    #   (call (gas) 0xF126 0 0 0 0 0)
    # }
    contract_24 = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=contract_25,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=Op.GAS,
            address=contract_25,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #     ; ccc...ccc  revert and suicide contract
    #     (call (gas) (+ 0x1000 $4) 0 0 0 0 0x40)
    #
    #     ; Write the returned results, if any
    #     [[0]] @0x00
    #     [[1]] @0x20
    # }
    contract_26 = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x4),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.STOP,
    )
    # Source: lll
    # {  ; RECURSE_VALID   RECURSE_INVALID
    #    (def 'NOP 0)
    #
    #    ; Read storage cell zero, so the first time we read it to won't
    #    ; be added to the cost
    #    @@0
    #
    #    ; Write to [[0xBEEF]], and see how much gas that cost. It should
    #    ; cost more when it is not declared storage
    #      [0]   (gas)
    #     [[0xBEEF]]  0x02
    #      [0]   (- @0 (gas) 17)
    #
    #    ; Read [[0x60A7]], and see how much gas that cost. It should
    #    ; cost more when it is not declared storage
    #    [0x20] (gas)
    #    [0xA0] @@0x60A7
    #    [0x20] (- @0x20 (gas) 35)
    #
    #    ; Write to a different cell each time
    #    [0x40] (gas)
    #    [[(+ 0xF000 @@0)]] 0xBEEF
    #    [0x40] (- @0x40 (gas) 0x78)
    #
    #    ; Read from a different cell each time
    #    [0x60] (gas)
    #    @@(+ 0xF010 @@0)
    #    [0x60] (- @0x60 (gas) 0x7a)
    #
    #
    # ... (13 more lines)
    contract_17 = pre.deploy_contract(
        code=Op.POP(Op.SLOAD(key=0x0))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0xBEEF, value=0x2)
        + Op.MSTORE(
            offset=0x0,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
        )
        + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.MSTORE(offset=0xA0, value=Op.SLOAD(key=0x60A7))
        + Op.MSTORE(
            offset=0x20,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x20), Op.GAS), 0x23),
        )
        + Op.MSTORE(offset=0x40, value=Op.GAS)
        + Op.SSTORE(key=Op.ADD(0xF000, Op.SLOAD(key=0x0)), value=0xBEEF)
        + Op.MSTORE(
            offset=0x40,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x40), Op.GAS), 0x78),
        )
        + Op.MSTORE(offset=0x60, value=Op.GAS)
        + Op.POP(Op.SLOAD(key=Op.ADD(0xF010, Op.SLOAD(key=0x0))))
        + Op.MSTORE(
            offset=0x60,
            value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x60), Op.GAS), 0x7A),
        )
        + Op.SSTORE(
            key=Op.ADD(0x100, Op.SLOAD(key=0x0)), value=Op.MLOAD(offset=0x0)
        )
        + Op.SSTORE(
            key=Op.ADD(0x200, Op.SLOAD(key=0x0)), value=Op.MLOAD(offset=0x20)
        )
        + Op.SSTORE(
            key=Op.ADD(0x300, Op.SLOAD(key=0x0)), value=Op.MLOAD(offset=0x40)
        )
        + Op.SSTORE(
            key=Op.ADD(0x400, Op.SLOAD(key=0x0)), value=Op.MLOAD(offset=0x60)
        )
        + Conditional(
            condition=Op.GT(Op.SLOAD(key=0x0), 0x0),
            if_true=Op.SSTORE(key=0x0, value=Op.SUB(Op.SLOAD(key=0x0), 0x1))
            + Op.POP(Op.CALL(address=Op.ADDRESS)),
        )
        + Op.STOP,
        storage={0: 15, 24743: 57005},
        balance=0xDE0B6B3A7640000,
    )

    # EIP-8037/8038 reprice several access components. With an empty
    # reservoir (the case here) the state-gas portion spills back into
    # regular gas, which `Op.GAS` observes. Derive each delta from the
    # fork's own gas model so it is exactly 0 pre-EIP-8037 and tracks
    # parameter changes.
    def create_initcode(
        creator: Address, head: tuple[int, int], tail: tuple[int, int]
    ) -> bytes:
        """
        Return the init code a creator assembles from its own code.

        `head` (offset, size) is copied to memory 0 and `tail` to 0x100.
        """
        account = pre[creator]
        assert account is not None
        code = bytes(account.code)
        return (
            code[head[0] : head[0] + head[1]].ljust(0x100, b"\0")
            + code[tail[0] : tail[0] + tail[1]]
        )

    created_18 = compute_create_address(address=contract_18, nonce=1)
    created_20 = compute_create_address(address=contract_20, nonce=1)
    created_22 = compute_create_address(address=contract_22, nonce=1)
    created_19 = compute_create2_address(
        contract_19,
        CREATE2_SALT,
        create_initcode(contract_19, (0x3C, 0x21), (0x36, 0x6)),
    )
    created_21 = compute_create2_address(
        contract_21,
        CREATE2_SALT,
        create_initcode(contract_21, (0x5A, 0xF), (0x47, 0x13)),
    )
    created_23 = compute_create2_address(
        contract_23,
        CREATE2_SALT,
        create_initcode(contract_23, (0x5A, 0x21), (0x47, 0x13)),
    )

    gas_costs = fork.gas_costs()

    def _sstore_delta(**metadata: int) -> int:
        op = Op.SSTORE.with_metadata(**metadata)
        return op.gas_cost(fork) - op.gas_cost(Cancun)

    # Fresh SSTORE-set (state-gas spill dominates), warm vs cold key.
    warm_set_delta = _sstore_delta(key_warm=True, current_value=0, new_value=2)
    cold_set_delta = _sstore_delta(
        key_warm=False, current_value=0, new_value=2
    )
    # CALL value transfer to a non-alive account: the Cancun NEW_ACCOUNT
    # base becomes a spilling state-gas charge.
    new_account_delta = (
        (fork.create_state_gas() - Cancun.gas_costs().NEW_ACCOUNT)
        if fork.is_eip_enabled(8037)
        else 0
    )
    # Cold account access reprice (0 pre-Amsterdam).
    cold_account_delta = (
        gas_costs.COLD_ACCOUNT_ACCESS - Cancun.gas_costs().COLD_ACCOUNT_ACCESS
    )
    # Cold storage access (SLOAD) reprice (0 pre-Amsterdam).
    cold_storage_delta = (
        gas_costs.COLD_STORAGE_ACCESS - Cancun.gas_costs().COLD_STORAGE_ACCESS
    )
    # SELFDESTRUCT to a non-alive cold beneficiary: new-account spill,
    # the new ACCOUNT_WRITE charge (0 pre-Amsterdam), and the cold
    # reprice.
    suicide_new_delta = (
        new_account_delta + gas_costs.ACCOUNT_WRITE + cold_account_delta
    )
    # callWriteSuicide measures a warm SSTORE-set then that SELFDESTRUCT.
    suicide_write_delta = warm_set_delta + suicide_new_delta

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={0: 2, 1: (20003 + warm_set_delta), 2: 107}
                )
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 2,
                        1: (22103 + cold_set_delta),
                        2: 2107 + cold_storage_delta,
                    }
                )
            },
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_2: Account(
                    storage={0: 2, 1: (20003 + warm_set_delta), 2: 107}
                )
            },
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_2: Account(
                    storage={
                        0: 2,
                        1: (22103 + cold_set_delta),
                        2: 2107 + cold_storage_delta,
                    }
                )
            },
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_3: Account(
                    storage={
                        0: 2,
                        1: (22103 + cold_set_delta),
                        2: 2107 + cold_storage_delta,
                        24743: 57005,
                    }
                )
            },
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_3: Account(
                    storage={
                        0: 2,
                        1: (20003 + warm_set_delta),
                        2: 107,
                        24743: 57005,
                    }
                )
            },
        },
        {
            "indexes": {"data": [6], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_4: Account(storage={0: 2107 + cold_storage_delta})
            },
        },
        {
            "indexes": {"data": [7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_4: Account(storage={0: 107})},
        },
        {
            "indexes": {"data": [8], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_26: Account(
                    storage={0: (20003 + warm_set_delta), 1: 100}
                )
            },
        },
        {
            "indexes": {"data": [9], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_26: Account(
                    storage={
                        0: (22103 + cold_set_delta),
                        1: 2100 + cold_storage_delta,
                    }
                )
            },
        },
        {
            "indexes": {"data": [10], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_7: Account(storage={0: (20001 + suicide_write_delta)})
            },
        },
        {
            "indexes": {"data": [11], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_7: Account(
                    storage={
                        0: (
                            24601
                            + cold_set_delta
                            + suicide_new_delta
                            + cold_account_delta
                        )
                    }
                )
            },
        },
        {
            "indexes": {"data": [12], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_9: Account(storage={0: 100 + suicide_new_delta})
            },
        },
        {
            "indexes": {"data": [13], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_9: Account(
                    storage={
                        0: 4600
                        + suicide_new_delta
                        + cold_account_delta
                        + cold_storage_delta
                    }
                )
            },
        },
        {
            "indexes": {"data": [14, 15], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_11: Account(storage={0: 2989})},
        },
        {
            "indexes": {"data": [16], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_14: Account(storage={0: 24589})},
        },
        {
            "indexes": {"data": [17], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_14: Account(storage={0: 2989})},
        },
        {
            "indexes": {"data": [18], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_16: Account(storage={0: 24589, 24743: 57005})},
        },
        {
            "indexes": {"data": [19], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_16: Account(storage={0: 2989, 24743: 57005})},
        },
        {
            "indexes": {"data": [20], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_17: Account(
                    storage={
                        0: 0,
                        256: 103,
                        257: 103,
                        258: 103,
                        259: 103,
                        260: 103,
                        261: 103,
                        262: 103,
                        263: 103,
                        264: 103,
                        265: 103,
                        266: 103,
                        267: 103,
                        268: 103,
                        269: 103,
                        270: 103,
                        271: (20003 + warm_set_delta),
                        512: 100,
                        513: 100,
                        514: 100,
                        515: 100,
                        516: 100,
                        517: 100,
                        518: 100,
                        519: 100,
                        520: 100,
                        521: 100,
                        522: 100,
                        523: 100,
                        524: 100,
                        525: 100,
                        526: 100,
                        527: 100,
                        768: (20003 + warm_set_delta),
                        769: (20003 + warm_set_delta),
                        770: (20003 + warm_set_delta),
                        771: (20003 + warm_set_delta),
                        772: (20003 + warm_set_delta),
                        773: (20003 + warm_set_delta),
                        774: (20003 + warm_set_delta),
                        775: (20003 + warm_set_delta),
                        776: (20003 + warm_set_delta),
                        777: (20003 + warm_set_delta),
                        778: (20003 + warm_set_delta),
                        779: (20003 + warm_set_delta),
                        780: (20003 + warm_set_delta),
                        781: (20003 + warm_set_delta),
                        782: (20003 + warm_set_delta),
                        783: (20003 + warm_set_delta),
                        1024: 100,
                        1025: 100,
                        1026: 100,
                        1027: 100,
                        1028: 100,
                        1029: 100,
                        1030: 100,
                        1031: 100,
                        1032: 100,
                        1033: 100,
                        1034: 100,
                        1035: 100,
                        1036: 100,
                        1037: 100,
                        1038: 100,
                        1039: 100,
                        24743: 57005,
                        48879: 2,
                        61440: 48879,
                        61441: 48879,
                        61442: 48879,
                        61443: 48879,
                        61444: 48879,
                        61445: 48879,
                        61446: 48879,
                        61447: 48879,
                        61448: 48879,
                        61449: 48879,
                        61450: 48879,
                        61451: 48879,
                        61452: 48879,
                        61453: 48879,
                        61454: 48879,
                        61455: 48879,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [21], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_17: Account(
                    storage={
                        0: 0,
                        256: 103,
                        257: 103,
                        258: 103,
                        259: 103,
                        260: 103,
                        261: 103,
                        262: 103,
                        263: 103,
                        264: 103,
                        265: 103,
                        266: 103,
                        267: 103,
                        268: 103,
                        269: 103,
                        270: 103,
                        271: (22103 + cold_set_delta),
                        512: 100,
                        513: 100,
                        514: 100,
                        515: 100,
                        516: 100,
                        517: 100,
                        518: 100,
                        519: 100,
                        520: 100,
                        521: 100,
                        522: 100,
                        523: 100,
                        524: 100,
                        525: 100,
                        526: 100,
                        527: 2100 + cold_storage_delta,
                        768: (22103 + cold_set_delta),
                        769: (22103 + cold_set_delta),
                        770: (22103 + cold_set_delta),
                        771: (22103 + cold_set_delta),
                        772: (22103 + cold_set_delta),
                        773: (22103 + cold_set_delta),
                        774: (22103 + cold_set_delta),
                        775: (22103 + cold_set_delta),
                        776: (22103 + cold_set_delta),
                        777: (22103 + cold_set_delta),
                        778: (22103 + cold_set_delta),
                        779: (22103 + cold_set_delta),
                        780: (22103 + cold_set_delta),
                        781: (22103 + cold_set_delta),
                        782: (22103 + cold_set_delta),
                        783: (22103 + cold_set_delta),
                        1024: 2100 + cold_storage_delta,
                        1025: 2100 + cold_storage_delta,
                        1026: 2100 + cold_storage_delta,
                        1027: 2100 + cold_storage_delta,
                        1028: 2100 + cold_storage_delta,
                        1029: 2100 + cold_storage_delta,
                        1030: 2100 + cold_storage_delta,
                        1031: 2100 + cold_storage_delta,
                        1032: 2100 + cold_storage_delta,
                        1033: 2100 + cold_storage_delta,
                        1034: 2100 + cold_storage_delta,
                        1035: 2100 + cold_storage_delta,
                        1036: 2100 + cold_storage_delta,
                        1037: 2100 + cold_storage_delta,
                        1038: 2100 + cold_storage_delta,
                        1039: 2100 + cold_storage_delta,
                        24743: 57005,
                        48879: 2,
                        61440: 48879,
                        61441: 48879,
                        61442: 48879,
                        61443: 48879,
                        61444: 48879,
                        61445: 48879,
                        61446: 48879,
                        61447: 48879,
                        61448: 48879,
                        61449: 48879,
                        61450: 48879,
                        61451: 48879,
                        61452: 48879,
                        61453: 48879,
                        61454: 48879,
                        61455: 48879,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [22], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                created_18: Account(
                    storage={0: 65535, 1: (20017 + warm_set_delta)}
                ),
            },
        },
        {
            "indexes": {"data": [23], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                created_18: Account(
                    storage={0: 65535, 1: (22117 + cold_set_delta)}
                ),
            },
        },
        {
            "indexes": {"data": [24], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                created_19: Account(
                    storage={0: 65535, 1: (20017 + warm_set_delta)}
                ),
            },
        },
        {
            "indexes": {"data": [25], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                created_19: Account(
                    storage={0: 65535, 1: (22117 + cold_set_delta)}
                ),
            },
        },
        {
            "indexes": {"data": [26], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                created_20: Account(
                    storage={0: 65535, 1: (20017 + warm_set_delta)}
                ),
            },
        },
        {
            "indexes": {"data": [27], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                created_20: Account(
                    storage={0: 65535, 1: (22117 + cold_set_delta)}
                ),
            },
        },
        {
            "indexes": {"data": [28], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                created_21: Account(
                    storage={0: 65535, 1: (20017 + warm_set_delta)}
                ),
            },
        },
        {
            "indexes": {"data": [29], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                created_21: Account(
                    storage={0: 65535, 1: (22117 + cold_set_delta)}
                ),
            },
        },
        {
            "indexes": {"data": [30], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                created_22: Account(
                    storage={0: 65535, 1: (20017 + warm_set_delta), 2: 117}
                ),
            },
        },
        {
            "indexes": {"data": [31], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                created_22: Account(
                    storage={0: 65535, 1: (22117 + cold_set_delta), 2: 117}
                ),
            },
        },
        {
            "indexes": {"data": [32], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                created_23: Account(
                    storage={0: 65535, 1: (20017 + warm_set_delta), 2: 117}
                ),
            },
        },
        {
            "indexes": {"data": [33], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                created_23: Account(
                    storage={0: 65535, 1: (22117 + cold_set_delta), 2: 117}
                ),
            },
        },
        {
            "indexes": {"data": [34], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_25: Account(
                    storage={0: 24743, 1: (20017 + warm_set_delta), 2: 117}
                )
            },
        },
        {
            "indexes": {"data": [35], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_25: Account(
                    storage={0: 24743, 1: (22117 + cold_set_delta), 2: 117}
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(contract_0, left_padding=True),
        Bytes("693c6139") + Hash(contract_0, left_padding=True),
        Bytes("693c6139") + Hash(contract_2, left_padding=True),
        Bytes("693c6139") + Hash(contract_2, left_padding=True),
        Bytes("693c6139") + Hash(contract_1, left_padding=True),
        Bytes("693c6139") + Hash(contract_1, left_padding=True),
        Bytes("693c6139") + Hash(contract_4, left_padding=True),
        Bytes("693c6139") + Hash(contract_4, left_padding=True),
        Bytes("693c6139") + Hash(contract_6, left_padding=True),
        Bytes("693c6139") + Hash(contract_6, left_padding=True),
        Bytes("693c6139") + Hash(contract_7, left_padding=True),
        Bytes("693c6139") + Hash(contract_7, left_padding=True),
        Bytes("693c6139") + Hash(contract_9, left_padding=True),
        Bytes("693c6139") + Hash(contract_9, left_padding=True),
        Bytes("693c6139") + Hash(contract_11, left_padding=True),
        Bytes("693c6139") + Hash(contract_11, left_padding=True),
        Bytes("693c6139") + Hash(contract_13, left_padding=True),
        Bytes("693c6139") + Hash(contract_13, left_padding=True),
        Bytes("693c6139") + Hash(contract_15, left_padding=True),
        Bytes("693c6139") + Hash(contract_15, left_padding=True),
        Bytes("693c6139") + Hash(contract_17, left_padding=True),
        Bytes("693c6139") + Hash(contract_17, left_padding=True),
        Bytes("693c6139") + Hash(contract_18, left_padding=True),
        Bytes("693c6139") + Hash(contract_18, left_padding=True),
        Bytes("693c6139") + Hash(contract_19, left_padding=True),
        Bytes("693c6139") + Hash(contract_19, left_padding=True),
        Bytes("693c6139") + Hash(contract_20, left_padding=True),
        Bytes("693c6139") + Hash(contract_20, left_padding=True),
        Bytes("693c6139") + Hash(contract_21, left_padding=True),
        Bytes("693c6139") + Hash(contract_21, left_padding=True),
        Bytes("693c6139") + Hash(contract_22, left_padding=True),
        Bytes("693c6139") + Hash(contract_22, left_padding=True),
        Bytes("693c6139") + Hash(contract_23, left_padding=True),
        Bytes("693c6139") + Hash(contract_23, left_padding=True),
        Bytes("693c6139") + Hash(contract_24, left_padding=True),
        Bytes("693c6139") + Hash(contract_24, left_padding=True),
    ]
    tx_value = [100000]
    tx_access_lists: dict[int, list] = {
        0: [
            AccessList(
                address=contract_0,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        1: [
            AccessList(
                address=contract_3,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        2: [
            AccessList(
                address=contract_2,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        3: [
            AccessList(
                address=contract_3,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        4: [
            AccessList(
                address=contract_1,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        5: [
            AccessList(
                address=contract_3,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        6: [
            AccessList(
                address=contract_4,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        7: [
            AccessList(
                address=contract_5,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        8: [
            AccessList(
                address=contract_6,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        9: [
            AccessList(
                address=contract_26,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        10: [
            AccessList(
                address=contract_8,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        11: [
            AccessList(
                address=contract_7,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        12: [
            AccessList(
                address=contract_10,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        13: [
            AccessList(
                address=contract_9,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        14: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000000000),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        15: [
            AccessList(
                address=contract_12,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        16: [
            AccessList(
                address=contract_14,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        17: [
            AccessList(
                address=contract_13,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        18: [
            AccessList(
                address=contract_16,
                storage_keys=[
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        19: [
            AccessList(
                address=contract_15,
                storage_keys=[
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        20: [
            AccessList(
                address=contract_17,
                storage_keys=[
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000beef"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f001"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f002"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f003"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f004"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f005"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f006"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f007"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f008"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f009"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f00a"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f00b"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f00c"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f00d"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f00e"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f00f"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f010"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f011"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f012"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f013"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f014"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f015"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f016"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f017"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f018"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f019"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f01a"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f01b"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f01c"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f01d"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f01e"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000f01f"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        21: [
            AccessList(
                address=Address(0xF000000000000000000000000000000000000116),
                storage_keys=[
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000beef"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        22: [
            AccessList(
                address=created_18,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        23: [
            AccessList(
                address=created_18,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        24: [
            AccessList(
                address=created_19,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        25: [
            AccessList(
                address=created_18,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        26: [
            AccessList(
                address=created_20,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        27: [
            AccessList(
                address=created_20,
                storage_keys=[
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000ffff"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        28: [
            AccessList(
                address=created_21,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        29: [
            AccessList(
                address=created_20,
                storage_keys=[
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000ffff"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        30: [
            AccessList(
                address=created_22,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        31: [
            AccessList(
                address=created_20,
                storage_keys=[
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000ffff"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        32: [
            AccessList(
                address=created_23,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        33: [
            AccessList(
                address=created_20,
                storage_keys=[
                    Hash(
                        "0x000000000000000000000000000000000000000000000000000000000000ffff"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        34: [
            AccessList(
                address=contract_25,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        35: [
            AccessList(
                address=contract_25,
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000020"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
    }

    tx = Transaction(
        sender=sender,
        to=contract_26,
        data=tx_data[d],
        state_gas_reservoir=0,
        value=tx_value[v],
        access_list=tx_access_lists.get(d),
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
