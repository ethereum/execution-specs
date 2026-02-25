"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stStackTests/underflowTestFiller.yml

callee code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup6
    stop

callee_1 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    mulmod
    stop

callee_2 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    sgt
    stop

callee_3 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup15
    stop

callee_4 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap5
    stop

callee_5 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup7
    stop

callee_6 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    and
    stop

callee_7 code:
    push1 0x01
    push1 0x01
    sstore
    not
    stop

callee_8 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    dup2
    stop

callee_9 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    sha3
    stop

callee_10 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    pop
    stop

callee_11 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    signextend
    stop

callee_12 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    create
    stop

callee_13 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup16
    stop

callee_14 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    log0
    stop

callee_15 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    smod
    stop

callee_16 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap4
    stop

callee_17 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap12
    stop

callee_18 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    byte
    stop

callee_19 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    ... (2 more instructions)

callee_20 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    signextend
    stop

callee_21 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap14
    stop

callee_22 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    log3
    stop

callee_23 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    addmod
    stop

callee_24 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    lt
    stop

callee_25 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap10
    stop

callee_26 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    eq
    stop

callee_27 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    dup3
    stop

callee_28 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup15
    stop

callee_29 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup14
    stop

callee_30 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    add
    stop

callee_31 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap9
    stop

callee_32 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    log2
    stop

callee_33 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap11
    stop

callee_34 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup10
    stop

callee_35 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap8
    stop

callee_36 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    staticcall
    stop

callee_37 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    calldataload
    stop

callee_38 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    xor
    stop

contract code:
    push2 0x60a7
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x04
    calldataload
    gas
    call
    pop
    push2 0x60a7
    push1 0x01
    sstore
    stop

callee_39 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup10
    stop

callee_40 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    mod
    stop

callee_41 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    eq
    stop

callee_42 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    sload
    stop

callee_43 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    codecopy
    stop

callee_44 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    dup1
    stop

callee_45 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    balance
    stop

callee_46 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    sdiv
    stop

callee_47 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    calldatacopy
    stop

callee_48 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup5
    stop

callee_49 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    dup4
    stop

callee_50 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup9
    stop

callee_51 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    mod
    stop

callee_52 code:
    push1 0x01
    push1 0x01
    sstore
    pop
    stop

callee_53 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap7
    stop

callee_54 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    dup3
    stop

callee_55 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup8
    stop

callee_56 code:
    push1 0x01
    push1 0x01
    sstore
    extcodesize
    stop

callee_57 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap12
    stop

callee_58 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    swap1
    stop

callee_59 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup12
    stop

callee_60 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap16
    ... (1 more instructions)

callee_61 code:
    push1 0x01
    push1 0x01
    sstore
    blockhash
    stop

callee_62 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    shl
    stop

callee_63 code:
    push1 0x01
    push1 0x01
    sstore
    extcodehash
    stop

callee_64 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    log4
    stop

callee_65 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap10
    stop

callee_66 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap14
    stop

callee_67 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap11
    stop

callee_68 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup11
    stop

callee_69 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap13
    stop

callee_70 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    extcodesize
    stop

callee_71 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    lt
    stop

callee_72 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    delegatecall
    stop

callee_73 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    log4
    stop

callee_74 code:
    push1 0x01
    push1 0x01
    sstore
    sload
    stop

callee_75 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    return
    stop

callee_76 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    or
    stop

callee_77 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup4
    stop

callee_78 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    div
    stop

callee_79 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    return
    stop

callee_80 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    codecopy
    stop

callee_81 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    mstore8
    stop

callee_82 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    swap1
    stop

callee_83 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    call
    stop

callee_84 code:
    push1 0x01
    push1 0x01
    sstore
    dup1
    stop

callee_85 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    callcode
    stop

callee_86 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    sar
    stop

callee_87 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap15
    ... (1 more instructions)

callee_88 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup13
    stop

callee_89 code:
    push1 0x01
    push1 0x01
    sstore
    mload
    stop

callee_90 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    create2
    stop

callee_91 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    delegatecall
    stop

callee_92 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    extcodecopy
    stop

callee_93 code:
    push1 0x01
    push1 0x01
    sstore
    balance
    stop

callee_94 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    exp
    stop

callee_95 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    swap3
    stop

callee_96 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup6
    stop

callee_97 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    xor
    stop

callee_98 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap7
    stop

callee_99 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    create
    stop

callee_100 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup16
    ... (1 more instructions)

callee_101 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    smod
    stop

callee_102 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap5
    stop

callee_103 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    mstore8
    stop

callee_104 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    extcodehash
    stop

callee_105 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    shr
    stop

callee_106 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    shl
    stop

callee_107 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    log3
    stop

callee_108 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    mstore
    stop

callee_109 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    swap2
    stop

callee_110 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup9
    stop

callee_111 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    callcode
    stop

callee_112 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    mload
    stop

callee_113 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    sar
    stop

callee_114 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap4
    stop

callee_115 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    sub
    stop

callee_116 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    blockhash
    stop

callee_117 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    calldatacopy
    stop

callee_118 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    iszero
    stop

callee_119 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    extcodecopy
    stop

callee_120 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap13
    stop

callee_121 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    shr
    stop

callee_122 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    sdiv
    stop

callee_123 code:
    push1 0x01
    push1 0x01
    sstore
    calldataload
    stop

callee_124 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    exp
    stop

callee_125 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap6
    stop

callee_126 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    addmod
    stop

callee_127 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    not
    stop

callee_128 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup12
    stop

callee_129 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    log1
    stop

callee_130 code:
    push1 0x01
    push1 0x01
    sstore
    iszero
    stop

callee_131 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    slt
    stop

callee_132 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    and
    stop

callee_133 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup7
    stop

callee_134 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    add
    stop

callee_135 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    sgt
    stop

callee_136 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap15
    stop

callee_137 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    log1
    stop

callee_138 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap6
    stop

callee_139 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    div
    stop

callee_140 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup11
    stop

callee_141 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    gt
    stop

callee_142 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap3
    stop

callee_143 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap9
    stop

callee_144 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    mulmod
    stop

callee_145 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    mul
    stop

callee_146 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    log2
    stop

callee_147 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    swap8
    stop

callee_148 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    mul
    stop

callee_149 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    slt
    stop

callee_150 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup5
    stop

callee_151 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    dup2
    stop

callee_152 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    or
    stop

callee_153 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    swap2
    stop

callee_154 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    mstore
    stop

callee_155 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    sha3
    stop

callee_156 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    staticcall
    stop

callee_157 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    byte
    stop

callee_158 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    create2
    stop

callee_159 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup13
    stop

callee_160 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    call
    stop

callee_161 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup14
    stop

callee_162 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    gt
    stop

callee_163 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    log0
    stop

callee_164 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    push1 0x80
    dup8
    stop

callee_165 code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x80
    push1 0x80
    sub
    stop
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stStackTests/underflowTestFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c61390000000000000000000000003aac251f428dcd7cb57e01c7dbb8bc3a76d5d628",
        "693c6139000000000000000000000000cc44bebaeb76a6568aa26ae045f8516fa29b0f9c",
        "693c6139000000000000000000000000c51017527cdd990d0c8e146ed36237694024021c",
        "693c613900000000000000000000000023d790b6f14975963ee30ff45cc4621c7e1eeaf7",
        "693c61390000000000000000000000001029b338aa781a64308000fa49515769618f176e",
        "693c6139000000000000000000000000c8d2eb10090f9940b7e816e6a278ae2ec943d232",
        "693c6139000000000000000000000000943b918e625b3ecb5d186d820a60c8eebd1c71ec",
        "693c613900000000000000000000000058a413dde8ddd92c793fca0b18ce89bd3dfba0e8",
        "693c61390000000000000000000000006f72794f9c9d8a693ff6c1134d611d353678fcf0",
        "693c6139000000000000000000000000b8479583829f24d888a0493a9132845b3d6a5305",
        "693c61390000000000000000000000001be71f78fcfbc7e4002db615e7fc878e7f090c50",
        "693c6139000000000000000000000000f04fe60ad6f92fa14a53a0882943a66ea4e49ef1",
        "693c6139000000000000000000000000f465862e7bf5085fb692e16d3181afaba87550cc",
        "693c61390000000000000000000000008ce099e0d9e5e5153e578f7cbfa9fd071b714142",
        "693c61390000000000000000000000008e3ab300e3d93ac55727c65510ff8bd96ea76928",
        "693c6139000000000000000000000000af6ead2e1a296b787d4b084d30b0733518fd2462",
        "693c613900000000000000000000000059f8c0328e432df7467313742e1effc9ee2bac4e",
        "693c6139000000000000000000000000bc57a2f2490132b8f8980cd242f7dc76b4b3f1c3",
        "693c6139000000000000000000000000c24790535cfea9781d66d59b81d9b92a576bb9ef",
        "693c6139000000000000000000000000488a9b0f0e885b96f67c113f0979799f801d70d3",
        "693c613900000000000000000000000050a33da19f003aec73bc65754e12a7f94c9b1c34",
        "693c6139000000000000000000000000866777eaddc2be0a50b3d3f76f2064876ea42802",
        "693c613900000000000000000000000016a80f6c0bbed421a0d6b392e891a52fca715213",
        "693c61390000000000000000000000009bd8e7c30198bd73a39e51d6866b72026272773e",
        "693c6139000000000000000000000000933cb75e0e03a16aa3d3e7114d269a6fe4db46f9",
        "693c6139000000000000000000000000f1cfc656c8d8e2bcfdfea0e0e9cabcc0b743dd19",
        "693c6139000000000000000000000000799721e570bcd85be50c0d7a399af369be561fbe",
        "693c61390000000000000000000000009386c3cce8cab9f8c3bc1a89c82a0e55588ced9d",
        "693c6139000000000000000000000000d54c502b5478a191e9a25bc0d1ba94669c5a5f4f",
        "693c6139000000000000000000000000836d0c3ce82596908935c3cc794da4603e135b1c",
        "693c61390000000000000000000000008ceb89e3037b7ac8b58e3765ea3eb65f1a9e4a7c",
        "693c61390000000000000000000000005782c86be10d218c82d509f3257e9dfdbf6dead8",
        "693c6139000000000000000000000000444a2203a30517f4a8becca90192b193a7b6ecf3",
        "693c61390000000000000000000000004da0082f56c3cae860eb6fb0fe36bc17cfba2c27",
        "693c6139000000000000000000000000d5765c6e58b373df78d7311fe80a67de0ddf987e",
        "693c6139000000000000000000000000742bf896d715c00eb77f340fcaa65bacaee2467c",
        "693c6139000000000000000000000000c698050f674750bbcafa30c433633dee22b8a9d3",
        "693c61390000000000000000000000006ce1b9fedca232f6829f0831ed2c23bd9c2f99a2",
        "693c613900000000000000000000000091605658e9533e831c9f855874faa14c363dc795",
        "693c6139000000000000000000000000f2578fadcdd5cd7b55f7046c88a7a77e195a7b17",
        "693c613900000000000000000000000034fb465a898787f7ed08bc2f5de86a896f8bc4da",
        "693c6139000000000000000000000000f84f405591be4ab47ca2ca1841dcb57cc43f076f",
        "693c61390000000000000000000000002cd79f853ec648b7c3ec3fac7c7ce82d7d83ea1e",
        "693c61390000000000000000000000000cd1b3e02e0bc556b0c7d4779c69a9a383c0c7cd",
        "693c6139000000000000000000000000175de68007e136237a4f26b6983dbce27a87fb5b",
        "693c61390000000000000000000000009c8fc002a1dcd0edcf93c20dc9d674031dc5a28d",
        "693c6139000000000000000000000000e6d703c31f83bc617a62f78e3c3a615001d3dd2c",
        "693c6139000000000000000000000000113855e9aa747f6ae6fd74667d7a288b2288caf6",
        "693c61390000000000000000000000002c2938555e004cbb0ce4481bad8a15857d983d06",
        "693c613900000000000000000000000063e21ad1535b95aaeed05e893b5b7947d6b0f15a",
        "693c61390000000000000000000000005bce589f39f0eff323bcbeac539dc9fd0f429bd2",
        "693c61390000000000000000000000008030a1eb20b388143f12fb547b5e53a4c164a621",
        "693c61390000000000000000000000005bb0e367bec7d734cb0fc9c27eb85af479b39673",
        "693c6139000000000000000000000000e594a68387d42d18bb8e460cef74876f05985e3a",
        "693c61390000000000000000000000009a90a463d916b189eee17b331f27a54142b79961",
        "693c6139000000000000000000000000029d8125096a81237be857845270ab34afab88ac",
        "693c61390000000000000000000000000d423fa4896aca0a02cba41462e754c3241427f0",
        "693c6139000000000000000000000000ca098deb4ab81002cddbd3c93261d6d1cb5113b5",
        "693c6139000000000000000000000000fbc09ac707fcca4ae8e348f01457ea18825bd139",
        "693c6139000000000000000000000000662d9872215dde44ec296918a0fd96c45c97b332",
        "693c6139000000000000000000000000aeec863f85b9a222ac1ffff774a881d46ec3ad37",
        "693c61390000000000000000000000005d4fa1456fbf03872b922dc0e8e48ec49f5faf9e",
        "693c61390000000000000000000000002b3bc02cabba968640fd86614f855a406b5c32e2",
        "693c61390000000000000000000000005029d082367aa4510d5a6e3b5cf83cd41e05c7f4",
        "693c6139000000000000000000000000c36332f339266d7989b005864c48548883213125",
        "693c6139000000000000000000000000973b5cc7e4678bcb85618b38c910f8adc68703a6",
        "693c613900000000000000000000000093d0507f681ba7de662d14ae8de922d161698c8e",
        "693c6139000000000000000000000000bf337119d0b966cc500cd3ff5ab9f3c7fddaa91d",
        "693c61390000000000000000000000007142d01ed8802179659127719398fa679ac41292",
        "693c6139000000000000000000000000a3d5aecbf6541cd2a0df5ae2e1294abc682180e6",
        "693c6139000000000000000000000000664f23c7af786dc61b6a068b3f9bde0051716384",
        "693c613900000000000000000000000075a2a8afa2446ec88a716ef7074351accfaccadf",
        "693c6139000000000000000000000000f9a965915f18a6108b842a40148dc5fd47ec7140",
        "693c6139000000000000000000000000d60ab3d73fd71f071ede5eead527db298236b162",
        "693c6139000000000000000000000000c744cf16cf5e2eb3c97e641e63801b8af3015def",
        "693c6139000000000000000000000000be25986eb0ee281252e783918d867630e5119455",
        "693c613900000000000000000000000017f25a871ea2ea564cffe99d31dedcf1fcff0a63",
        "693c6139000000000000000000000000fb5dbfcd64b16ab0129b99278b9d5ccfb9b605b9",
        "693c6139000000000000000000000000c70e97b872035f925b07db55b85a3eac04e724d6",
        "693c6139000000000000000000000000d051afb76160844eb32df55e052044de76250ebc",
        "693c6139000000000000000000000000dac05b6fc9dc9c0b65ecc5032f2313f7a7dd2586",
        "693c61390000000000000000000000003fd249e0be1d7bf6386b7dc90d92bf95f9f98bc4",
        "693c6139000000000000000000000000a7eec8574dbfc883575f2b20a80f14f335a809b6",
        "693c613900000000000000000000000022d7d32459b46a9b69542c31545cb3a0d887064c",
        "693c6139000000000000000000000000715f213243cd7baeefd3a52434353015a4fc8de2",
        "693c613900000000000000000000000079d8aedd70f8a99a15e3083d3335a028d69af9fa",
        "693c613900000000000000000000000077225976113d69eee2fd870ea02d670badabdcab",
        "693c61390000000000000000000000002947a82b8aabd0f80c7e215bc066ea92bdd65b31",
        "693c613900000000000000000000000092bfb1aa73e92c1f591d8b6854514df6672bbb90",
        "693c6139000000000000000000000000b2e76a6fdfc66a93a2354748ec2d107a818fe73c",
        "693c61390000000000000000000000005df0dd6d100e8dd03d211b55d4a8cc7c7657c038",
        "693c61390000000000000000000000004e985c32a0f53ab426fe2bcdea720f0f71a4c1d1",
        "693c6139000000000000000000000000ec26e590a6f5da137088aee0c4d6b0f8870eb1ad",
        "693c6139000000000000000000000000ac95d1d1c86af90f5a0cf44c104d0da04ab3a467",
        "693c6139000000000000000000000000a1903db9aa9aa2665ca7da383db9291d93f1d576",
        "693c6139000000000000000000000000891e304c4126f24bf762df079c7683420b16ff57",
        "693c6139000000000000000000000000e383f3e5b45fa86d5b37cdfeb146cf903641c76c",
        "693c6139000000000000000000000000da3ec48d60f1cf78ecc154fa0c6181cf833916aa",
        "693c61390000000000000000000000000824de5bb894849fcdd60634275d6bcb8157d4a0",
        "693c6139000000000000000000000000da24ffd288756277e556671ae2306b7587ef0c63",
        "693c613900000000000000000000000010df9321d0355308a994d3709e30609bd72655b7",
        "693c6139000000000000000000000000c52f28d6433f203eae23f5f2fc642938a25aafe7",
        "693c61390000000000000000000000007d00c3c2cbb3b64bbb4f0f518ef779f6df875f6e",
        "693c6139000000000000000000000000e8565720ba47032e7b0edcb4bce06303f83ff450",
        "693c61390000000000000000000000005f750bad38b37c4ebcc5fee4eed5639283a09a38",
        "693c613900000000000000000000000014ed6c71ebccdf69007d79fe699d368102533929",
        "693c613900000000000000000000000084798b4fb35d09db14ecab9d65a4a280e483fe29",
        "693c61390000000000000000000000007d002cacbe954f4360fe634fbe23f5b67c686cbf",
        "693c6139000000000000000000000000b37c41d445866ceb36edc4e6456cae78949c9f97",
        "693c61390000000000000000000000008e689eee6c7387a37612a42f8ee44dd7a823fb5c",
        "693c6139000000000000000000000000c131d96e30386b63f89592008939dd517579f203",
        "693c613900000000000000000000000058cd7cc2b1b1cd459decc8ebbbd2fcbf9c68cef9",
        "693c6139000000000000000000000000cc9ffede5b0d7f58002f852181d0b4b35c0dabee",
        "693c61390000000000000000000000000bdf35fc6c5c2a3e1e9711112ff7ef71e2419532",
        "693c6139000000000000000000000000ec8b92806c1ad0f2dcf5b0207db7eddb464df0ca",
        "693c613900000000000000000000000011ffe11bb835b6ce89fc91d65b1f6c0919b07a1d",
        "693c6139000000000000000000000000a7b1cd72ebc0b8f3e353885ef17b04aa28d8f0fa",
        "693c6139000000000000000000000000701a7d6aa6ef15a38fd8311e074a96c09b434a2a",
        "693c6139000000000000000000000000c024f0f81b1c2c1ab6362e5ecf79a7be3de2f60e",
        "693c6139000000000000000000000000a49e66f497a85d949d334a20724bc6b75da3d3ae",
        "693c61390000000000000000000000001e27cc27790c60dde31215bf2be1d9a66c41c8fa",
        "693c61390000000000000000000000001523b84a9fb4a0d32f070847190d34f912c04c4e",
        "693c61390000000000000000000000007aedaf23d4e9afb84baa67824cebfec01339afc1",
        "693c61390000000000000000000000005096db6b2ea6ace8e2aeb3610faaad183a51ca8d",
        "693c6139000000000000000000000000e519ac21322361b960bed6ccbbf538840e85f76e",
        "693c6139000000000000000000000000c74809261edc3edd91ec17dbf4b898233c42ddb4",
        "693c61390000000000000000000000009d8ea14af8d401208eb0687b8ae6f1e5ed6808d4",
        "693c613900000000000000000000000018c875e7eb21e50bad81e8940a2272fd6760e0dd",
        "693c6139000000000000000000000000ee8790666225df6f97ae194e20853f2907bbaebc",
        "693c613900000000000000000000000045952ed2c957691ae4de05032b429a8a0f0ced5b",
        "693c6139000000000000000000000000b50944b674eb20b0fe99a18bb764b45500c41144",
        "693c6139000000000000000000000000fcc0a7ebcab4f6d8c91c9062f2cd1148073253d2",
        "693c61390000000000000000000000008b62b65db3bd1be727290b490c679c0e84585498",
        "693c61390000000000000000000000006c6bc4f9ccde5da559a3e5dddb6b60a8675c0076",
        "693c61390000000000000000000000002ac63027195da2ee9ce4cc1dff225ca97d3c2f0c",
        "693c6139000000000000000000000000723a69480f074f5df2544cacf63347fb5f0f36d1",
        "693c613900000000000000000000000073f7599a216d98d9ff1559788a9771d78895a6a3",
        "693c61390000000000000000000000004289634ebf793179377faa7140610bb80db21b45",
        "693c613900000000000000000000000066a62a0af37886b9b057a1bad714665525e7687f",
        "693c61390000000000000000000000001bb096578fe2f1be79e03ea88551a8bdd0692bea",
        "693c6139000000000000000000000000745a759f45602915eab7bdc87bc8d1c1675d4e29",
        "693c6139000000000000000000000000bf99ad09fc2f72924cbe6da6020f985e65f78901",
        "693c6139000000000000000000000000727fd27941dbe4d8f1e2e9daa0df70288fd73772",
        "693c61390000000000000000000000001eb3790937f47fe31a45f55bd82f50107e7a463a",
        "693c6139000000000000000000000000cd63f547ee166a3feb23a945f488ccc5ee921eef",
        "693c61390000000000000000000000008fd69485a26470a721f6dd7e685da39ee2a3dc1c",
        "693c61390000000000000000000000006f631ae51ead55c8526aff13665fe5dd055e3561",
        "693c61390000000000000000000000001debd2afba875db8938ce64218b40fb210e1de0a",
        "693c6139000000000000000000000000e98c1ab0ff23d5c5005c639781d1a635b9af887b",
        "693c6139000000000000000000000000acda51eb0d678a0d52bfa44e4354d8f371f43438",
        "693c61390000000000000000000000009768a9bb367830f3331b0c09d7183c131e44a7fc",
        "693c6139000000000000000000000000d6bb0ea7c7f60c967d3deeeaaba555daafbc52cb",
        "693c613900000000000000000000000019598106d1cede298b275523e64593c95d5c431c",
        "693c6139000000000000000000000000b44c7350f24bb5482057b53911a1d3c91c263eaf",
        "693c61390000000000000000000000000d0e14670e6e8718377bc2fae6b6814d558d3dee",
        "693c6139000000000000000000000000a15fe2669809ddc6640e94572907a53411b2aa6e",
        "693c6139000000000000000000000000d435f13e92f7db306b9b32e1d61db6ecd9c135bd",
        "693c6139000000000000000000000000c3fce336558080ef8b1a20a209b173e6d163e548",
        "693c6139000000000000000000000000620d85c5acc41cbfa47a763bbb9e326054b1819d",
        "693c61390000000000000000000000009b9d04770c429114574c11780fc9658d3257e80b",
        "693c613900000000000000000000000044c420a5b1a9071eb7ff6f1027c167c002c7f355",
        "693c6139000000000000000000000000dcb6a7c9b64471effdd8bbf72d32d271deeec8c5",
        "693c6139000000000000000000000000d9292de838cd8839d91b496d8a9d25ac102cd821",
        "693c61390000000000000000000000003ad6053af54d703f7e7229bd5bf120c908c8513d",
        "693c61390000000000000000000000004c47590ab3f1dfe486900d0ec41510f85545b182",
        "693c61390000000000000000000000009b0edd3cf5b6ccc09b3c9d15646ef629a7767ba8",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11', 'case12', 'case13', 'case14', 'case15', 'case16', 'case17', 'case18', 'case19', 'case20', 'case21', 'case22', 'case23', 'case24', 'case25', 'case26', 'case27', 'case28', 'case29', 'case30', 'case31', 'case32', 'case33', 'case34', 'case35', 'case36', 'case37', 'case38', 'case39', 'case40', 'case41', 'case42', 'case43', 'case44', 'case45', 'case46', 'case47', 'case48', 'case49', 'case50', 'case51', 'case52', 'case53', 'case54', 'case55', 'case56', 'case57', 'case58', 'case59', 'case60', 'case61', 'case62', 'case63', 'case64', 'case65', 'case66', 'case67', 'case68', 'case69', 'case70', 'case71', 'case72', 'case73', 'case74', 'case75', 'case76', 'case77', 'case78', 'case79', 'case80', 'case81', 'case82', 'case83', 'case84', 'case85', 'case86', 'case87', 'case88', 'case89', 'case90', 'case91', 'case92', 'case93', 'case94', 'case95', 'case96', 'case97', 'case98', 'case99', 'case100', 'case101', 'case102', 'case103', 'case104', 'case105', 'case106', 'case107', 'case108', 'case109', 'case110', 'case111', 'case112', 'case113', 'case114', 'case115', 'case116', 'case117', 'case118', 'case119', 'case120', 'case121', 'case122', 'case123', 'case124', 'case125', 'case126', 'case127', 'case128', 'case129', 'case130', 'case131', 'case132', 'case133', 'case134', 'case135', 'case136', 'case137', 'case138', 'case139', 'case140', 'case141', 'case142', 'case143', 'case144', 'case145', 'case146', 'case147', 'case148', 'case149', 'case150', 'case151', 'case152', 'case153', 'case154', 'case155', 'case156', 'case157', 'case158', 'case159', 'case160', 'case161', 'case162', 'case163', 'case164', 'case165'],
)
@pytest.mark.pre_alloc_mutable
def test_underflow_test(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x56724d001b4f2a2888a81971a64aad37cd43f881")
    contract = Address("0x4c5f839d523e76fc3837e085a3e1538cd36e288a")
    callee = Address("0x029d8125096a81237be857845270ab34afab88ac")
    callee_1 = Address("0x0824de5bb894849fcdd60634275d6bcb8157d4a0")
    callee_2 = Address("0x0bdf35fc6c5c2a3e1e9711112ff7ef71e2419532")
    callee_3 = Address("0x0cd1b3e02e0bc556b0c7d4779c69a9a383c0c7cd")
    callee_4 = Address("0x0d0e14670e6e8718377bc2fae6b6814d558d3dee")
    callee_5 = Address("0x0d423fa4896aca0a02cba41462e754c3241427f0")
    callee_6 = Address("0x1029b338aa781a64308000fa49515769618f176e")
    callee_7 = Address("0x10df9321d0355308a994d3709e30609bd72655b7")
    callee_8 = Address("0x113855e9aa747f6ae6fd74667d7a288b2288caf6")
    callee_9 = Address("0x11ffe11bb835b6ce89fc91d65b1f6c0919b07a1d")
    callee_10 = Address("0x14ed6c71ebccdf69007d79fe699d368102533929")
    callee_11 = Address("0x1523b84a9fb4a0d32f070847190d34f912c04c4e")
    callee_12 = Address("0x16a80f6c0bbed421a0d6b392e891a52fca715213")
    callee_13 = Address("0x175de68007e136237a4f26b6983dbce27a87fb5b")
    callee_14 = Address("0x17f25a871ea2ea564cffe99d31dedcf1fcff0a63")
    callee_15 = Address("0x18c875e7eb21e50bad81e8940a2272fd6760e0dd")
    callee_16 = Address("0x19598106d1cede298b275523e64593c95d5c431c")
    callee_17 = Address("0x1bb096578fe2f1be79e03ea88551a8bdd0692bea")
    callee_18 = Address("0x1be71f78fcfbc7e4002db615e7fc878e7f090c50")
    callee_19 = Address("0x1debd2afba875db8938ce64218b40fb210e1de0a")
    callee_20 = Address("0x1e27cc27790c60dde31215bf2be1d9a66c41c8fa")
    callee_21 = Address("0x1eb3790937f47fe31a45f55bd82f50107e7a463a")
    callee_22 = Address("0x22d7d32459b46a9b69542c31545cb3a0d887064c")
    callee_23 = Address("0x23d790b6f14975963ee30ff45cc4621c7e1eeaf7")
    callee_24 = Address("0x2947a82b8aabd0f80c7e215bc066ea92bdd65b31")
    callee_25 = Address("0x2ac63027195da2ee9ce4cc1dff225ca97d3c2f0c")
    callee_26 = Address("0x2b3bc02cabba968640fd86614f855a406b5c32e2")
    callee_27 = Address("0x2c2938555e004cbb0ce4481bad8a15857d983d06")
    callee_28 = Address("0x2cd79f853ec648b7c3ec3fac7c7ce82d7d83ea1e")
    callee_29 = Address("0x34fb465a898787f7ed08bc2f5de86a896f8bc4da")
    callee_30 = Address("0x3aac251f428dcd7cb57e01c7dbb8bc3a76d5d628")
    callee_31 = Address("0x3ad6053af54d703f7e7229bd5bf120c908c8513d")
    callee_32 = Address("0x3fd249e0be1d7bf6386b7dc90d92bf95f9f98bc4")
    callee_33 = Address("0x4289634ebf793179377faa7140610bb80db21b45")
    callee_34 = Address("0x444a2203a30517f4a8becca90192b193a7b6ecf3")
    callee_35 = Address("0x44c420a5b1a9071eb7ff6f1027c167c002c7f355")
    callee_36 = Address("0x45952ed2c957691ae4de05032b429a8a0f0ced5b")
    callee_37 = Address("0x488a9b0f0e885b96f67c113f0979799f801d70d3")
    callee_38 = Address("0x4c47590ab3f1dfe486900d0ec41510f85545b182")
    callee_39 = Address("0x4da0082f56c3cae860eb6fb0fe36bc17cfba2c27")
    callee_40 = Address("0x4e985c32a0f53ab426fe2bcdea720f0f71a4c1d1")
    callee_41 = Address("0x5029d082367aa4510d5a6e3b5cf83cd41e05c7f4")
    callee_42 = Address("0x5096db6b2ea6ace8e2aeb3610faaad183a51ca8d")
    callee_43 = Address("0x50a33da19f003aec73bc65754e12a7f94c9b1c34")
    callee_44 = Address("0x5782c86be10d218c82d509f3257e9dfdbf6dead8")
    callee_45 = Address("0x58a413dde8ddd92c793fca0b18ce89bd3dfba0e8")
    callee_46 = Address("0x58cd7cc2b1b1cd459decc8ebbbd2fcbf9c68cef9")
    callee_47 = Address("0x59f8c0328e432df7467313742e1effc9ee2bac4e")
    callee_48 = Address("0x5bb0e367bec7d734cb0fc9c27eb85af479b39673")
    callee_49 = Address("0x5bce589f39f0eff323bcbeac539dc9fd0f429bd2")
    callee_50 = Address("0x5d4fa1456fbf03872b922dc0e8e48ec49f5faf9e")
    callee_51 = Address("0x5df0dd6d100e8dd03d211b55d4a8cc7c7657c038")
    callee_52 = Address("0x5f750bad38b37c4ebcc5fee4eed5639283a09a38")
    callee_53 = Address("0x620d85c5acc41cbfa47a763bbb9e326054b1819d")
    callee_54 = Address("0x63e21ad1535b95aaeed05e893b5b7947d6b0f15a")
    callee_55 = Address("0x662d9872215dde44ec296918a0fd96c45c97b332")
    callee_56 = Address("0x664f23c7af786dc61b6a068b3f9bde0051716384")
    callee_57 = Address("0x66a62a0af37886b9b057a1bad714665525e7687f")
    callee_58 = Address("0x6c6bc4f9ccde5da559a3e5dddb6b60a8675c0076")
    callee_59 = Address("0x6ce1b9fedca232f6829f0831ed2c23bd9c2f99a2")
    callee_60 = Address("0x6f631ae51ead55c8526aff13665fe5dd055e3561")
    callee_61 = Address("0x6f72794f9c9d8a693ff6c1134d611d353678fcf0")
    callee_62 = Address("0x701a7d6aa6ef15a38fd8311e074a96c09b434a2a")
    callee_63 = Address("0x7142d01ed8802179659127719398fa679ac41292")
    callee_64 = Address("0x715f213243cd7baeefd3a52434353015a4fc8de2")
    callee_65 = Address("0x723a69480f074f5df2544cacf63347fb5f0f36d1")
    callee_66 = Address("0x727fd27941dbe4d8f1e2e9daa0df70288fd73772")
    callee_67 = Address("0x73f7599a216d98d9ff1559788a9771d78895a6a3")
    callee_68 = Address("0x742bf896d715c00eb77f340fcaa65bacaee2467c")
    callee_69 = Address("0x745a759f45602915eab7bdc87bc8d1c1675d4e29")
    callee_70 = Address("0x75a2a8afa2446ec88a716ef7074351accfaccadf")
    callee_71 = Address("0x77225976113d69eee2fd870ea02d670badabdcab")
    callee_72 = Address("0x799721e570bcd85be50c0d7a399af369be561fbe")
    callee_73 = Address("0x79d8aedd70f8a99a15e3083d3335a028d69af9fa")
    callee_74 = Address("0x7aedaf23d4e9afb84baa67824cebfec01339afc1")
    callee_75 = Address("0x7d002cacbe954f4360fe634fbe23f5b67c686cbf")
    callee_76 = Address("0x7d00c3c2cbb3b64bbb4f0f518ef779f6df875f6e")
    callee_77 = Address("0x8030a1eb20b388143f12fb547b5e53a4c164a621")
    callee_78 = Address("0x836d0c3ce82596908935c3cc794da4603e135b1c")
    callee_79 = Address("0x84798b4fb35d09db14ecab9d65a4a280e483fe29")
    callee_80 = Address("0x866777eaddc2be0a50b3d3f76f2064876ea42802")
    callee_81 = Address("0x891e304c4126f24bf762df079c7683420b16ff57")
    callee_82 = Address("0x8b62b65db3bd1be727290b490c679c0e84585498")
    callee_83 = Address("0x8ce099e0d9e5e5153e578f7cbfa9fd071b714142")
    callee_84 = Address("0x8ceb89e3037b7ac8b58e3765ea3eb65f1a9e4a7c")
    callee_85 = Address("0x8e3ab300e3d93ac55727c65510ff8bd96ea76928")
    callee_86 = Address("0x8e689eee6c7387a37612a42f8ee44dd7a823fb5c")
    callee_87 = Address("0x8fd69485a26470a721f6dd7e685da39ee2a3dc1c")
    callee_88 = Address("0x91605658e9533e831c9f855874faa14c363dc795")
    callee_89 = Address("0x92bfb1aa73e92c1f591d8b6854514df6672bbb90")
    callee_90 = Address("0x933cb75e0e03a16aa3d3e7114d269a6fe4db46f9")
    callee_91 = Address("0x9386c3cce8cab9f8c3bc1a89c82a0e55588ced9d")
    callee_92 = Address("0x93d0507f681ba7de662d14ae8de922d161698c8e")
    callee_93 = Address("0x943b918e625b3ecb5d186d820a60c8eebd1c71ec")
    callee_94 = Address("0x973b5cc7e4678bcb85618b38c910f8adc68703a6")
    callee_95 = Address("0x9768a9bb367830f3331b0c09d7183c131e44a7fc")
    callee_96 = Address("0x9a90a463d916b189eee17b331f27a54142b79961")
    callee_97 = Address("0x9b0edd3cf5b6ccc09b3c9d15646ef629a7767ba8")
    callee_98 = Address("0x9b9d04770c429114574c11780fc9658d3257e80b")
    callee_99 = Address("0x9bd8e7c30198bd73a39e51d6866b72026272773e")
    callee_100 = Address("0x9c8fc002a1dcd0edcf93c20dc9d674031dc5a28d")
    callee_101 = Address("0x9d8ea14af8d401208eb0687b8ae6f1e5ed6808d4")
    callee_102 = Address("0xa15fe2669809ddc6640e94572907a53411b2aa6e")
    callee_103 = Address("0xa1903db9aa9aa2665ca7da383db9291d93f1d576")
    callee_104 = Address("0xa3d5aecbf6541cd2a0df5ae2e1294abc682180e6")
    callee_105 = Address("0xa49e66f497a85d949d334a20724bc6b75da3d3ae")
    callee_106 = Address("0xa7b1cd72ebc0b8f3e353885ef17b04aa28d8f0fa")
    callee_107 = Address("0xa7eec8574dbfc883575f2b20a80f14f335a809b6")
    callee_108 = Address("0xac95d1d1c86af90f5a0cf44c104d0da04ab3a467")
    callee_109 = Address("0xacda51eb0d678a0d52bfa44e4354d8f371f43438")
    callee_110 = Address("0xaeec863f85b9a222ac1ffff774a881d46ec3ad37")
    callee_111 = Address("0xaf6ead2e1a296b787d4b084d30b0733518fd2462")
    callee_112 = Address("0xb2e76a6fdfc66a93a2354748ec2d107a818fe73c")
    callee_113 = Address("0xb37c41d445866ceb36edc4e6456cae78949c9f97")
    callee_114 = Address("0xb44c7350f24bb5482057b53911a1d3c91c263eaf")
    callee_115 = Address("0xb50944b674eb20b0fe99a18bb764b45500c41144")
    callee_116 = Address("0xb8479583829f24d888a0493a9132845b3d6a5305")
    callee_117 = Address("0xbc57a2f2490132b8f8980cd242f7dc76b4b3f1c3")
    callee_118 = Address("0xbe25986eb0ee281252e783918d867630e5119455")
    callee_119 = Address("0xbf337119d0b966cc500cd3ff5ab9f3c7fddaa91d")
    callee_120 = Address("0xbf99ad09fc2f72924cbe6da6020f985e65f78901")
    callee_121 = Address("0xc024f0f81b1c2c1ab6362e5ecf79a7be3de2f60e")
    callee_122 = Address("0xc131d96e30386b63f89592008939dd517579f203")
    callee_123 = Address("0xc24790535cfea9781d66d59b81d9b92a576bb9ef")
    callee_124 = Address("0xc36332f339266d7989b005864c48548883213125")
    callee_125 = Address("0xc3fce336558080ef8b1a20a209b173e6d163e548")
    callee_126 = Address("0xc51017527cdd990d0c8e146ed36237694024021c")
    callee_127 = Address("0xc52f28d6433f203eae23f5f2fc642938a25aafe7")
    callee_128 = Address("0xc698050f674750bbcafa30c433633dee22b8a9d3")
    callee_129 = Address("0xc70e97b872035f925b07db55b85a3eac04e724d6")
    callee_130 = Address("0xc744cf16cf5e2eb3c97e641e63801b8af3015def")
    callee_131 = Address("0xc74809261edc3edd91ec17dbf4b898233c42ddb4")
    callee_132 = Address("0xc8d2eb10090f9940b7e816e6a278ae2ec943d232")
    callee_133 = Address("0xca098deb4ab81002cddbd3c93261d6d1cb5113b5")
    callee_134 = Address("0xcc44bebaeb76a6568aa26ae045f8516fa29b0f9c")
    callee_135 = Address("0xcc9ffede5b0d7f58002f852181d0b4b35c0dabee")
    callee_136 = Address("0xcd63f547ee166a3feb23a945f488ccc5ee921eef")
    callee_137 = Address("0xd051afb76160844eb32df55e052044de76250ebc")
    callee_138 = Address("0xd435f13e92f7db306b9b32e1d61db6ecd9c135bd")
    callee_139 = Address("0xd54c502b5478a191e9a25bc0d1ba94669c5a5f4f")
    callee_140 = Address("0xd5765c6e58b373df78d7311fe80a67de0ddf987e")
    callee_141 = Address("0xd60ab3d73fd71f071ede5eead527db298236b162")
    callee_142 = Address("0xd6bb0ea7c7f60c967d3deeeaaba555daafbc52cb")
    callee_143 = Address("0xd9292de838cd8839d91b496d8a9d25ac102cd821")
    callee_144 = Address("0xda24ffd288756277e556671ae2306b7587ef0c63")
    callee_145 = Address("0xda3ec48d60f1cf78ecc154fa0c6181cf833916aa")
    callee_146 = Address("0xdac05b6fc9dc9c0b65ecc5032f2313f7a7dd2586")
    callee_147 = Address("0xdcb6a7c9b64471effdd8bbf72d32d271deeec8c5")
    callee_148 = Address("0xe383f3e5b45fa86d5b37cdfeb146cf903641c76c")
    callee_149 = Address("0xe519ac21322361b960bed6ccbbf538840e85f76e")
    callee_150 = Address("0xe594a68387d42d18bb8e460cef74876f05985e3a")
    callee_151 = Address("0xe6d703c31f83bc617a62f78e3c3a615001d3dd2c")
    callee_152 = Address("0xe8565720ba47032e7b0edcb4bce06303f83ff450")
    callee_153 = Address("0xe98c1ab0ff23d5c5005c639781d1a635b9af887b")
    callee_154 = Address("0xec26e590a6f5da137088aee0c4d6b0f8870eb1ad")
    callee_155 = Address("0xec8b92806c1ad0f2dcf5b0207db7eddb464df0ca")
    callee_156 = Address("0xee8790666225df6f97ae194e20853f2907bbaebc")
    callee_157 = Address("0xf04fe60ad6f92fa14a53a0882943a66ea4e49ef1")
    callee_158 = Address("0xf1cfc656c8d8e2bcfdfea0e0e9cabcc0b743dd19")
    callee_159 = Address("0xf2578fadcdd5cd7b55f7046c88a7a77e195a7b17")
    callee_160 = Address("0xf465862e7bf5085fb692e16d3181afaba87550cc")
    callee_161 = Address("0xf84f405591be4ab47ca2ca1841dcb57cc43f076f")
    callee_162 = Address("0xf9a965915f18a6108b842a40148dc5fd47ec7140")
    callee_163 = Address("0xfb5dbfcd64b16ab0129b99278b9d5ccfb9b605b9")
    callee_164 = Address("0xfbc09ac707fcca4ae8e348f01457ea18825bd139")
    callee_165 = Address("0xfcc0a7ebcab4f6d8c91c9062f2cd1148073253d2")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP6
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.MULMOD + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.SGT + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.DUP15 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_4] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP5 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_5] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP7
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_6] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.AND + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_7] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.NOT + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_8] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.DUP2 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_9] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.SHA3 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_10] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.POP + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_11] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.SIGNEXTEND + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_12] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.CREATE + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_13] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.DUP16 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_14] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.LOG0 + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_15] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.SMOD + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_16] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP4 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_17] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP12 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_18] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.BYTE + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_19] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP16 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_20] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.SIGNEXTEND
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_21] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.SWAP14 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_22] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.LOG3 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_23] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.ADDMOD + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_24] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.LT + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_25] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.SWAP10 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_26] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.EQ + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_27] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.DUP3 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_28] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP15
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_29] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP14 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_30] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.ADD + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_31] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP9 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_32] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.LOG2 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_33] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP11 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_34] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP10
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_35] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP8 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_36] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.STATICCALL + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_37] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.CALLDATALOAD
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_38] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.XOR + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH2[0x60a7] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.GAS + Op.CALL + Op.POP + Op.PUSH2[0x60a7]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_39] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP10 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_40] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.MOD + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_41] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.EQ + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_42] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.SLOAD + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_43] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.CODECOPY + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=0)
    pre[callee_44] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.DUP1 + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_45] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.BALANCE
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_46] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.SDIV + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_47] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.CALLDATACOPY + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_48] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP5 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_49] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.DUP4 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_50] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP9 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_51] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.MOD + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_52] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.POP + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_53] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.SWAP7 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_54] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.DUP3 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_55] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP8 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_56] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.EXTCODESIZE + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_57] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP12 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_58] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.SWAP1 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_59] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP12 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_60] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP16 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_61] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.BLOCKHASH + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_62] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.SHL + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_63] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.EXTCODEHASH + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_64] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.LOG4 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_65] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.SWAP10 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_66] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.SWAP14 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_67] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.SWAP11 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_68] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.DUP11 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_69] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP13 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_70] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.EXTCODESIZE
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_71] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.LT + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_72] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DELEGATECALL + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_73] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.LOG4
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_74] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.SLOAD + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_75] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.RETURN + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_76] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.OR + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_77] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP4 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_78] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.DIV + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_79] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.RETURN + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_80] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.CODECOPY + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_81] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.MSTORE8 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_82] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.SWAP1 + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_83] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.CALL + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_84] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.DUP1 + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_85] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.CALLCODE + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_86] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.SAR + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_87] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP15 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_88] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP13 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_89] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.MLOAD + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_90] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.CREATE2 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_91] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.DELEGATECALL + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_92] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.EXTCODECOPY + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_93] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.BALANCE + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_94] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.EXP + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_95] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.SWAP3 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_96] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP6 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_97] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.XOR + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_98] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP7 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_99] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.CREATE + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_100] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP16 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_101] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.SMOD + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_102] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP5
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_103] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.MSTORE8
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_104] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.EXTCODEHASH
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_105] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.SHR + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_106] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.SHL + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_107] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.LOG3 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_108] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.MSTORE + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_109] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.SWAP2 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_110] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP9 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_111] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.CALLCODE + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_112] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.MLOAD + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_113] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.SAR + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_114] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP4 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_115] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.SUB + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_116] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.BLOCKHASH
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_117] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.CALLDATACOPY + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_118] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.ISZERO + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_119] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.EXTCODECOPY + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_120] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.SWAP13 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_121] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.SHR + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_122] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.SDIV + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_123] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.CALLDATALOAD + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_124] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.EXP + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_125] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.SWAP6 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_126] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.ADDMOD + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_127] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.NOT + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_128] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.DUP12 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_129] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.LOG1 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_130] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.ISZERO + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_131] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.SLT + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_132] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.AND + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_133] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.DUP7 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_134] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.ADD + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_135] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.SGT + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_136] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.SWAP15 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_137] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.LOG1 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_138] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP6
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_139] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.DIV + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_140] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP11
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_141] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.GT + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_142] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP3 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_143] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP9
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_144] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.MULMOD + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_145] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.MUL + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_146] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.LOG2 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_147] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.SWAP8 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_148] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.MUL + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_149] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.SLT + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_150] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP5 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_151] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.DUP2 + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_152] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.OR + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_153] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.SWAP2 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_154] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.MSTORE + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_155] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.SHA3 + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_156] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.STATICCALL + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_157] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.BYTE + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_158] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.CREATE2 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_159] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP13 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_160] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.CALL
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_161] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.DUP14
        + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_162] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.GT + Op.STOP,
        storage={0x1: 0x60a7},
    )
    pre[callee_163] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.LOG0 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_164] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.DUP8 + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )
    pre[callee_165] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.SUB + Op.STOP
    ),
        storage={0x1: 0x60a7},
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x40ac0fc28c27e961ee46ec43355a094de205856edbd4654cf2577c2608d4ec1e"
        ),
        to=contract,
        data=tx_data,
        gas_limit=8000000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
