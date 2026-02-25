"""
Ported from:
tests/static/state_tests/VMTests/vmIOandFlowOperations/jumpToPushFiller.yml

callee code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x0a
    jump
    push1 0x5b
    jumpdest

callee_1 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push1 0x5b
    jumpdest

callee_2 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x0b
    jump
    push2 0x5b5b
    jumpdest

callee_3 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push2 0x5b5b
    jumpdest

callee_4 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x0a
    jump
    push2 0x5b5b
    jumpdest

callee_5 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x0c
    jump
    push3 0x5b5b5b
    jumpdest

callee_6 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push3 0x5b5b5b
    jumpdest

callee_7 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x0b
    jump
    push3 0x5b5b5b
    jumpdest

callee_8 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x0d
    jump
    push4 0x5b5b5b5b
    jumpdest

callee_9 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push4 0x5b5b5b5b
    jumpdest

callee_10 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x0c
    jump
    push4 0x5b5b5b5b
    jumpdest

callee_11 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x0e
    jump
    push5 0x5b5b5b5b5b
    jumpdest

callee_12 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push5 0x5b5b5b5b5b
    jumpdest

callee_13 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x0d
    jump
    push5 0x5b5b5b5b5b
    jumpdest

callee_14 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x0f
    jump
    push6 0x5b5b5b5b5b5b
    jumpdest

callee_15 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push6 0x5b5b5b5b5b5b
    jumpdest

callee_16 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x0e
    jump
    push6 0x5b5b5b5b5b5b
    jumpdest

callee_17 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x10
    jump
    push7 0x5b5b5b5b5b5b5b
    jumpdest

callee_18 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push7 0x5b5b5b5b5b5b5b
    jumpdest

callee_19 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x0f
    jump
    push7 0x5b5b5b5b5b5b5b
    jumpdest

callee_20 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x11
    jump
    push8 0x5b5b5b5b5b5b5b5b
    jumpdest

callee_21 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push8 0x5b5b5b5b5b5b5b5b
    jumpdest

callee_22 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x10
    jump
    push8 0x5b5b5b5b5b5b5b5b
    jumpdest

callee_23 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x12
    jump
    push9 0x5b5b5b5b5b5b5b5b5b
    jumpdest

callee_24 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push9 0x5b5b5b5b5b5b5b5b5b
    jumpdest

callee_25 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x11
    jump
    push9 0x5b5b5b5b5b5b5b5b5b
    jumpdest

callee_26 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x13
    jump
    push10 0x5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_27 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push10 0x5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_28 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x12
    jump
    push10 0x5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_29 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x14
    jump
    push11 0x5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_30 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push11 0x5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_31 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x13
    jump
    push11 0x5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_32 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x15
    jump
    push12 0x5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_33 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push12 0x5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_34 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x14
    jump
    push12 0x5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_35 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x16
    jump
    push13 0x5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_36 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push13 0x5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_37 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x15
    jump
    push13 0x5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_38 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x17
    jump
    push14 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_39 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push14 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_40 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x16
    jump
    push14 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_41 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x18
    jump
    push15 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_42 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push15 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_43 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x17
    jump
    push15 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_44 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x19
    jump
    push16 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_45 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push16 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_46 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x18
    jump
    push16 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_47 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x1a
    jump
    push17 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_48 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push17 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_49 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x19
    jump
    push17 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_50 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x1b
    jump
    push18 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_51 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push18 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_52 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x1a
    jump
    push18 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_53 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x1c
    jump
    push19 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_54 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push19 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_55 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x1b
    jump
    push19 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_56 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x1d
    jump
    push20 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_57 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push20 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_58 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x1c
    jump
    push20 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_59 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x1e
    jump
    push21 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_60 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push21 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_61 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x1d
    jump
    push21 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_62 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x1f
    jump
    push22 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_63 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push22 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_64 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x1e
    jump
    push22 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_65 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x20
    jump
    push23 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_66 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push23 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_67 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x1f
    jump
    push23 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_68 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x21
    jump
    push24 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_69 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push24 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_70 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x20
    jump
    push24 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_71 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x22
    jump
    push25 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_72 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push25 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_73 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x21
    jump
    push25 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_74 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x23
    jump
    push26 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_75 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push26 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_76 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x22
    jump
    push26 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_77 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x24
    jump
    push27 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_78 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push27 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_79 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x23
    jump
    push27 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_80 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x25
    jump
    push28 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_81 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push28 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_82 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x24
    jump
    push28 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_83 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x26
    jump
    push29 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_84 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push29 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_85 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x25
    jump
    push29 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_86 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x27
    jump
    push30 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_87 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push30 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_88 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x26
    jump
    push30 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_89 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x28
    jump
    push31 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_90 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push31 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_91 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x27
    jump
    push31 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_92 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x29
    jump
    push32 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_93 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x09
    jump
    push32 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

callee_94 code:
    push1 0x01
    push1 0x00
    sstore
    push1 0x28
    jump
    push32 0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b
    jumpdest

contract code:
    push1 0x00
    dup1
    dup1
    dup1
    push1 0x04
    calldataload
    push2 0x1388
    gas
    sub
    delegatecall
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
    ["tests/static/state_tests/VMTests/vmIOandFlowOperations/jumpToPushFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c613900000000000000000000000000000000000000000000000000000000000000ac",
        "693c613900000000000000000000000000000000000000000000000000000000000000bc",
        "693c613900000000000000000000000000000000000000000000000000000000000000cc",
        "693c613900000000000000000000000000000000000000000000000000000000000000dc",
        "693c613900000000000000000000000000000000000000000000000000000000000000ec",
        "693c613900000000000000000000000000000000000000000000000000000000000000fc",
        "693c6139000000000000000000000000000000000000000000000000000000000000010c",
        "693c6139000000000000000000000000000000000000000000000000000000000000011c",
        "693c6139000000000000000000000000000000000000000000000000000000000000012c",
        "693c6139000000000000000000000000000000000000000000000000000000000000013c",
        "693c6139000000000000000000000000000000000000000000000000000000000000014c",
        "693c6139000000000000000000000000000000000000000000000000000000000000015c",
        "693c6139000000000000000000000000000000000000000000000000000000000000016c",
        "693c6139000000000000000000000000000000000000000000000000000000000000017c",
        "693c6139000000000000000000000000000000000000000000000000000000000000018c",
        "693c6139000000000000000000000000000000000000000000000000000000000000019c",
        "693c6139000000000000000000000000000000000000000000000000000000000000020c",
        "693c6139000000000000000000000000000000000000000000000000000000000000001c",
        "693c6139000000000000000000000000000000000000000000000000000000000000002c",
        "693c6139000000000000000000000000000000000000000000000000000000000000003c",
        "693c6139000000000000000000000000000000000000000000000000000000000000002c",
        "693c6139000000000000000000000000000000000000000000000000000000000000004c",
        "693c6139000000000000000000000000000000000000000000000000000000000000005c",
        "693c6139000000000000000000000000000000000000000000000000000000000000006c",
        "693c6139000000000000000000000000000000000000000000000000000000000000007c",
        "693c6139000000000000000000000000000000000000000000000000000000000000008c",
        "693c6139000000000000000000000000000000000000000000000000000000000000009c",
        "693c613900000000000000000000000000000000000000000000000000000000000000ac",
        "693c613900000000000000000000000000000000000000000000000000000000000000bc",
        "693c613900000000000000000000000000000000000000000000000000000000000000cc",
        "693c613900000000000000000000000000000000000000000000000000000000000000dc",
        "693c6139000000000000000000000000000000000000000000000000000000000000003c",
        "693c613900000000000000000000000000000000000000000000000000000000000000ec",
        "693c613900000000000000000000000000000000000000000000000000000000000000fc",
        "693c6139000000000000000000000000000000000000000000000000000000000000010c",
        "693c6139000000000000000000000000000000000000000000000000000000000000011c",
        "693c6139000000000000000000000000000000000000000000000000000000000000012c",
        "693c6139000000000000000000000000000000000000000000000000000000000000013c",
        "693c6139000000000000000000000000000000000000000000000000000000000000014c",
        "693c6139000000000000000000000000000000000000000000000000000000000000015c",
        "693c6139000000000000000000000000000000000000000000000000000000000000016c",
        "693c6139000000000000000000000000000000000000000000000000000000000000017c",
        "693c6139000000000000000000000000000000000000000000000000000000000000004c",
        "693c6139000000000000000000000000000000000000000000000000000000000000018c",
        "693c6139000000000000000000000000000000000000000000000000000000000000019c",
        "693c6139000000000000000000000000000000000000000000000000000000000000020c",
        "693c6139000000000000000000000000000000000000000000000000000000000000005c",
        "693c6139000000000000000000000000000000000000000000000000000000000000006c",
        "693c6139000000000000000000000000000000000000000000000000000000000000007c",
        "693c6139000000000000000000000000000000000000000000000000000000000000008c",
        "693c6139000000000000000000000000000000000000000000000000000000000000009c",
        "693c6139000000000000000000000000000000000000000000000000000000000000001c",
        "693c613900000000000000000000000000000000000000000000000000000000000000aa",
        "693c613900000000000000000000000000000000000000000000000000000000000000ba",
        "693c613900000000000000000000000000000000000000000000000000000000000000ca",
        "693c613900000000000000000000000000000000000000000000000000000000000000da",
        "693c613900000000000000000000000000000000000000000000000000000000000000ea",
        "693c613900000000000000000000000000000000000000000000000000000000000000fa",
        "693c6139000000000000000000000000000000000000000000000000000000000000010a",
        "693c6139000000000000000000000000000000000000000000000000000000000000011a",
        "693c6139000000000000000000000000000000000000000000000000000000000000012a",
        "693c6139000000000000000000000000000000000000000000000000000000000000013a",
        "693c6139000000000000000000000000000000000000000000000000000000000000014a",
        "693c6139000000000000000000000000000000000000000000000000000000000000015a",
        "693c6139000000000000000000000000000000000000000000000000000000000000016a",
        "693c6139000000000000000000000000000000000000000000000000000000000000017a",
        "693c6139000000000000000000000000000000000000000000000000000000000000018a",
        "693c6139000000000000000000000000000000000000000000000000000000000000019a",
        "693c6139000000000000000000000000000000000000000000000000000000000000020a",
        "693c6139000000000000000000000000000000000000000000000000000000000000002a",
        "693c6139000000000000000000000000000000000000000000000000000000000000003a",
        "693c6139000000000000000000000000000000000000000000000000000000000000004a",
        "693c6139000000000000000000000000000000000000000000000000000000000000005a",
        "693c6139000000000000000000000000000000000000000000000000000000000000006a",
        "693c6139000000000000000000000000000000000000000000000000000000000000007a",
        "693c6139000000000000000000000000000000000000000000000000000000000000008a",
        "693c6139000000000000000000000000000000000000000000000000000000000000009a",
        "693c6139000000000000000000000000000000000000000000000000000000000000001a",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11', 'case12', 'case13', 'case14', 'case15', 'case16', 'case17', 'case18', 'case19', 'case20', 'case21', 'case22', 'case23', 'case24', 'case25', 'case26', 'case27', 'case28', 'case29', 'case30', 'case31', 'case32', 'case33', 'case34', 'case35', 'case36', 'case37', 'case38', 'case39', 'case40', 'case41', 'case42', 'case43', 'case44', 'case45', 'case46', 'case47', 'case48', 'case49', 'case50', 'case51', 'case52', 'case53', 'case54', 'case55', 'case56', 'case57', 'case58', 'case59', 'case60', 'case61', 'case62', 'case63', 'case64', 'case65', 'case66', 'case67', 'case68', 'case69', 'case70', 'case71', 'case72', 'case73', 'case74', 'case75', 'case76', 'case77'],
)
@pytest.mark.pre_alloc_mutable
def test_jump_to_push(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xcccccccccccccccccccccccccccccccccccccccc")
    callee = Address("0x000000000000000000000000000000000000001a")
    callee_1 = Address("0x000000000000000000000000000000000000001b")
    callee_2 = Address("0x000000000000000000000000000000000000002a")
    callee_3 = Address("0x000000000000000000000000000000000000002b")
    callee_4 = Address("0x000000000000000000000000000000000000002c")
    callee_5 = Address("0x000000000000000000000000000000000000003a")
    callee_6 = Address("0x000000000000000000000000000000000000003b")
    callee_7 = Address("0x000000000000000000000000000000000000003c")
    callee_8 = Address("0x000000000000000000000000000000000000004a")
    callee_9 = Address("0x000000000000000000000000000000000000004b")
    callee_10 = Address("0x000000000000000000000000000000000000004c")
    callee_11 = Address("0x000000000000000000000000000000000000005a")
    callee_12 = Address("0x000000000000000000000000000000000000005b")
    callee_13 = Address("0x000000000000000000000000000000000000005c")
    callee_14 = Address("0x000000000000000000000000000000000000006a")
    callee_15 = Address("0x000000000000000000000000000000000000006b")
    callee_16 = Address("0x000000000000000000000000000000000000006c")
    callee_17 = Address("0x000000000000000000000000000000000000007a")
    callee_18 = Address("0x000000000000000000000000000000000000007b")
    callee_19 = Address("0x000000000000000000000000000000000000007c")
    callee_20 = Address("0x000000000000000000000000000000000000008a")
    callee_21 = Address("0x000000000000000000000000000000000000008b")
    callee_22 = Address("0x000000000000000000000000000000000000008c")
    callee_23 = Address("0x000000000000000000000000000000000000009a")
    callee_24 = Address("0x000000000000000000000000000000000000009b")
    callee_25 = Address("0x000000000000000000000000000000000000009c")
    callee_26 = Address("0x00000000000000000000000000000000000000aa")
    callee_27 = Address("0x00000000000000000000000000000000000000ab")
    callee_28 = Address("0x00000000000000000000000000000000000000ac")
    callee_29 = Address("0x00000000000000000000000000000000000000ba")
    callee_30 = Address("0x00000000000000000000000000000000000000bb")
    callee_31 = Address("0x00000000000000000000000000000000000000bc")
    callee_32 = Address("0x00000000000000000000000000000000000000ca")
    callee_33 = Address("0x00000000000000000000000000000000000000cb")
    callee_34 = Address("0x00000000000000000000000000000000000000cc")
    callee_35 = Address("0x00000000000000000000000000000000000000da")
    callee_36 = Address("0x00000000000000000000000000000000000000db")
    callee_37 = Address("0x00000000000000000000000000000000000000dc")
    callee_38 = Address("0x00000000000000000000000000000000000000ea")
    callee_39 = Address("0x00000000000000000000000000000000000000eb")
    callee_40 = Address("0x00000000000000000000000000000000000000ec")
    callee_41 = Address("0x00000000000000000000000000000000000000fa")
    callee_42 = Address("0x00000000000000000000000000000000000000fb")
    callee_43 = Address("0x00000000000000000000000000000000000000fc")
    callee_44 = Address("0x000000000000000000000000000000000000010a")
    callee_45 = Address("0x000000000000000000000000000000000000010b")
    callee_46 = Address("0x000000000000000000000000000000000000010c")
    callee_47 = Address("0x000000000000000000000000000000000000011a")
    callee_48 = Address("0x000000000000000000000000000000000000011b")
    callee_49 = Address("0x000000000000000000000000000000000000011c")
    callee_50 = Address("0x000000000000000000000000000000000000012a")
    callee_51 = Address("0x000000000000000000000000000000000000012b")
    callee_52 = Address("0x000000000000000000000000000000000000012c")
    callee_53 = Address("0x000000000000000000000000000000000000013a")
    callee_54 = Address("0x000000000000000000000000000000000000013b")
    callee_55 = Address("0x000000000000000000000000000000000000013c")
    callee_56 = Address("0x000000000000000000000000000000000000014a")
    callee_57 = Address("0x000000000000000000000000000000000000014b")
    callee_58 = Address("0x000000000000000000000000000000000000014c")
    callee_59 = Address("0x000000000000000000000000000000000000015a")
    callee_60 = Address("0x000000000000000000000000000000000000015b")
    callee_61 = Address("0x000000000000000000000000000000000000015c")
    callee_62 = Address("0x000000000000000000000000000000000000016a")
    callee_63 = Address("0x000000000000000000000000000000000000016b")
    callee_64 = Address("0x000000000000000000000000000000000000016c")
    callee_65 = Address("0x000000000000000000000000000000000000017a")
    callee_66 = Address("0x000000000000000000000000000000000000017b")
    callee_67 = Address("0x000000000000000000000000000000000000017c")
    callee_68 = Address("0x000000000000000000000000000000000000018a")
    callee_69 = Address("0x000000000000000000000000000000000000018b")
    callee_70 = Address("0x000000000000000000000000000000000000018c")
    callee_71 = Address("0x000000000000000000000000000000000000019a")
    callee_72 = Address("0x000000000000000000000000000000000000019b")
    callee_73 = Address("0x000000000000000000000000000000000000019c")
    callee_74 = Address("0x00000000000000000000000000000000000001aa")
    callee_75 = Address("0x00000000000000000000000000000000000001ab")
    callee_76 = Address("0x00000000000000000000000000000000000001ac")
    callee_77 = Address("0x00000000000000000000000000000000000001ba")
    callee_78 = Address("0x00000000000000000000000000000000000001bb")
    callee_79 = Address("0x00000000000000000000000000000000000001bc")
    callee_80 = Address("0x00000000000000000000000000000000000001ca")
    callee_81 = Address("0x00000000000000000000000000000000000001cb")
    callee_82 = Address("0x00000000000000000000000000000000000001cc")
    callee_83 = Address("0x00000000000000000000000000000000000001da")
    callee_84 = Address("0x00000000000000000000000000000000000001db")
    callee_85 = Address("0x00000000000000000000000000000000000001dc")
    callee_86 = Address("0x00000000000000000000000000000000000001ea")
    callee_87 = Address("0x00000000000000000000000000000000000001eb")
    callee_88 = Address("0x00000000000000000000000000000000000001ec")
    callee_89 = Address("0x00000000000000000000000000000000000001fa")
    callee_90 = Address("0x00000000000000000000000000000000000001fb")
    callee_91 = Address("0x00000000000000000000000000000000000001fc")
    callee_92 = Address("0x000000000000000000000000000000000000020a")
    callee_93 = Address("0x000000000000000000000000000000000000020b")
    callee_94 = Address("0x000000000000000000000000000000000000020c")

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
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xa] + Op.JUMP
        + Op.PUSH1[0x5b] + Op.JUMPDEST
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH1[0x5b] + Op.JUMPDEST
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xb] + Op.JUMP
        + Op.PUSH2[0x5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH2[0x5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_4] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xa] + Op.JUMP
        + Op.PUSH2[0x5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_5] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xc] + Op.JUMP
        + Op.PUSH3[0x5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_6] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH3[0x5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_7] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xb] + Op.JUMP
        + Op.PUSH3[0x5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_8] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xd] + Op.JUMP
        + Op.PUSH4[0x5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_9] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH4[0x5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_10] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xc] + Op.JUMP
        + Op.PUSH4[0x5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_11] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xe] + Op.JUMP
        + Op.PUSH5[0x5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_12] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH5[0x5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_13] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xd] + Op.JUMP
        + Op.PUSH5[0x5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_14] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xf] + Op.JUMP
        + Op.PUSH6[0x5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH6[0x5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_16] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xe] + Op.JUMP
        + Op.PUSH6[0x5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_17] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x10] + Op.JUMP
        + Op.PUSH7[0x5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_18] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH7[0x5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_19] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0xf] + Op.JUMP
        + Op.PUSH7[0x5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_20] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x11] + Op.JUMP
        + Op.PUSH8[0x5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_21] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH8[0x5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_22] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x10] + Op.JUMP
        + Op.PUSH8[0x5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_23] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x12] + Op.JUMP
        + Op.PUSH9[0x5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_24] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH9[0x5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_25] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x11] + Op.JUMP
        + Op.PUSH9[0x5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_26] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x13] + Op.JUMP
        + Op.PUSH10[0x5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_27] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH10[0x5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_28] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x12] + Op.JUMP
        + Op.PUSH10[0x5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_29] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x14] + Op.JUMP
        + Op.PUSH11[0x5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_30] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH11[0x5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_31] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x13] + Op.JUMP
        + Op.PUSH11[0x5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_32] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x15] + Op.JUMP
        + Op.PUSH12[0x5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_33] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH12[0x5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_34] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x14] + Op.JUMP
        + Op.PUSH12[0x5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_35] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x16] + Op.JUMP
        + Op.PUSH13[0x5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_36] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH13[0x5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_37] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x15] + Op.JUMP
        + Op.PUSH13[0x5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_38] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x17] + Op.JUMP
        + Op.PUSH14[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_39] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH14[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_40] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x16] + Op.JUMP
        + Op.PUSH14[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_41] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x18] + Op.JUMP
        + Op.PUSH15[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_42] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH15[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_43] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x17] + Op.JUMP
        + Op.PUSH15[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_44] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x19] + Op.JUMP
        + Op.PUSH16[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_45] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH16[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_46] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x18] + Op.JUMP
        + Op.PUSH16[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_47] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1a] + Op.JUMP
        + Op.PUSH17[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_48] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH17[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_49] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x19] + Op.JUMP
        + Op.PUSH17[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_50] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1b] + Op.JUMP
        + Op.PUSH18[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_51] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH18[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_52] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1a] + Op.JUMP
        + Op.PUSH18[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_53] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1c] + Op.JUMP
        + Op.PUSH19[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_54] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH19[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_55] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1b] + Op.JUMP
        + Op.PUSH19[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_56] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1d] + Op.JUMP
        + Op.PUSH20[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_57] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH20[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_58] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1c] + Op.JUMP
        + Op.PUSH20[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_59] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1e] + Op.JUMP
        + Op.PUSH21[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_60] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH21[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_61] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1d] + Op.JUMP
        + Op.PUSH21[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_62] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1f] + Op.JUMP
        + Op.PUSH22[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_63] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH22[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_64] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1e] + Op.JUMP
        + Op.PUSH22[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_65] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x20] + Op.JUMP
        + Op.PUSH23[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_66] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH23[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_67] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1f] + Op.JUMP
        + Op.PUSH23[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_68] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x21] + Op.JUMP
        + Op.PUSH24[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_69] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH24[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_70] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x20] + Op.JUMP
        + Op.PUSH24[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b] + Op.JUMPDEST
    ),
    )
    pre[callee_71] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x22] + Op.JUMP
        + Op.PUSH25[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_72] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH25[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_73] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x21] + Op.JUMP
        + Op.PUSH25[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_74] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x23] + Op.JUMP
        + Op.PUSH26[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_75] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH26[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_76] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x22] + Op.JUMP
        + Op.PUSH26[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_77] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x24] + Op.JUMP
        + Op.PUSH27[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_78] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH27[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_79] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x23] + Op.JUMP
        + Op.PUSH27[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_80] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x25] + Op.JUMP
        + Op.PUSH28[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_81] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH28[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_82] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x24] + Op.JUMP
        + Op.PUSH28[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_83] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x26] + Op.JUMP
        + Op.PUSH29[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_84] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH29[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_85] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x25] + Op.JUMP
        + Op.PUSH29[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_86] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x27] + Op.JUMP
        + Op.PUSH30[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_87] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH30[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_88] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x26] + Op.JUMP
        + Op.PUSH30[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_89] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x28] + Op.JUMP
        + Op.PUSH31[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_90] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH31[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_91] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x27] + Op.JUMP
        + Op.PUSH31[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_92] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x29] + Op.JUMP
        + Op.PUSH32[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_93] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x9] + Op.JUMP
        + Op.PUSH32[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[callee_94] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x28] + Op.JUMP
        + Op.PUSH32[0x5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b]
        + Op.JUMPDEST
    ),
    )
    pre[sender] = Account(balance=0x100000000000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH2[0x1388] + Op.GAS + Op.SUB + Op.DELEGATECALL
        + Op.STOP
    ),
        storage={0x0: 0x0},
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
