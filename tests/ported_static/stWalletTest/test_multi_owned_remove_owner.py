"""
Test_multi_owned_remove_owner.

Ported from:
state_tests/stWalletTest/multiOwnedRemoveOwnerFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stWalletTest/multiOwnedRemoveOwnerFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_multi_owned_remove_owner(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_multi_owned_remove_owner."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x6295EE1B4F6DD65047762F924ECD367C17EABF8F)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw
    # 0x7c01000000000000000000000000000000000000000000000000000000006000350463173825d981146100655780632f54bf6e146100b75780637065cb48146100e8578063b75c7dc614610105578063ba51a6df14610142578063f00d4b5d1461015f57005b6101816004356000604060003680828437909120905061046d815b73ffffffffffffffffffffffffffffffffffffffff3316600090815261010260205260408120548180808381141561058f57610586565b6101876004355b73ffffffffffffffffffffffffffffffffffffffff16600090815261010260205260408120541190565b610181600435604060003680828437909120905061037c81610080565b61018160043573ffffffffffffffffffffffffffffffffffffffff3316600090815261010260205260408120549080808381141561019157610213565b610181600435604060003680828437909120905061053381610080565b6101816004356024356000604060003680828437909120905061028681610080565b60006000f35b8060005260206000f35b5050506000828152610103602052604081206001810154600284900a929083168190111561021357815460018084018054919092018455849003905573ffffffffffffffffffffffffffffffffffffffff3316604090815260608690527fc7fb647e59b18047309aa15aad418e5d7ca96d173ad704f1031a2c3d7591734b9080a15b5050505050565b015573ffffffffffffffffffffffffffffffffffffffff84811660008181526101026020526040808220829055928616808252908390208590559082526060527fb532073b38c83145e3e5135377a08bf9aab55bc0fd7c1179cd4fb995d2a5159c9080a15b505b505050565b1561027f57610294836100be565b1561029f5750610281565b73ffffffffffffffffffffffffffffffffffffffff84166000908152610102602052604081205492508214156102d55750610281565b6102f75b6101045460005b8181101561080c5761010480548290811061085457005b73ffffffffffffffffffffffffffffffffffffffff8316600283610100811061021a57005b015560015473ffffffffffffffffffffffffffffffffffffffff831660008181526101026020908152604091829020939093559081527f994a936646fe87ffe4f1e469d3d6aa417d6b855598397f323de5b449f765f0c39190a15b505b50565b156103775761038a826100be565b156103955750610379565b61039d6102d9565b60015460fa901015156103b4576103b26103cb565b505b60015460fa901015156103f55750610379565b6104255b600060015b6001548110156106f7575b600154811080156107535750600281610100811061074c57005b6001805481019081905573ffffffffffffffffffffffffffffffffffffffff831690600290610100811061031c57005b5073ffffffffffffffffffffffffffffffffffffffff831660409081527f58619076adf5bb0943d100ef88d52d7c3fd691b19d3a9071b555b651fbf418da90602090a1505050565b156102815773ffffffffffffffffffffffffffffffffffffffff83166000908152610102602052604081205492508214156104a85750610377565b60016001600050540360006000505411156104c35750610377565b600060028361010081106104d357005b015573ffffffffffffffffffffffffffffffffffffffff8316600090815261010260205260408120556103c76102d9565b60408281527facbdb084c721332ac59f9b8e392196c9eb0e4932862da8eb9beaf0dad4f550da90602090a15050565b15610377576001548211156105485750610379565b60008290556105046102d9565b82547fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff018355600183018054821790555b50505050919050565b600086815261010360205260408120805490945090925082141561061a5781548355600183810183905561010480549182018082558280158290116106a6578286527f4c0be60200faa20559308cb7b5a1bb3255c16cb1cab91f525b5ae7a03d02fabe9081019082015b808211156106a457600081556001016105f9565b6000918252602090912001555b506001820154600284900a908116600014156105865773ffffffffffffffffffffffffffffffffffffffff3316604090815260608790527fe1c52dc63b719ade82e8bea94cc41a0d5d28e4aaf536adb5e9cccc9ff8c1aeda9080a182546001901115156105555760008681526101036020526101048054604090922060020154909181106106c057005b505b505050600284018190556101048054889290811061060d57005b6000918252602080832090910182905587825261010390526040812081815560018181018390556002909101919091559450610586565b5090565b01546000145b1561076057600180547fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0190555b60018054118015610701575060015460029061010081106106fb57005b0154600014155b1561072f576001016103db565b600154811080156107845750600154600290610100811061077d57005b0154600014155b801561079f5750600281610100811061079957005b01546000145b156107b85760015460029061010081106107bd57005b01555b6103d0565b015460028261010081106107cd57005b015580610102600060028361010081106107e357005b01548152602081019190915260400160009081209190915560015460029061010081106107b557005b61010480546000808355919091527f4c0be60200faa20559308cb7b5a1bb3255c16cb1cab91f525b5ae7a03d02fabe908101905b8082111561027f5760008155600101610840565b60009182526020822001541415156108a6576101048054610103916000918490811061087c57005b60009182526020808320909101548352820192909252604001812081815560018101829055600201555b6001016102e056  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.DIV(
            Op.CALLDATALOAD(offset=0x0),
            0x100000000000000000000000000000000000000000000000000000000,
        )
        + Op.JUMPI(pc=Op.PUSH2[0x65], condition=Op.EQ(Op.DUP2, 0x173825D9))
        + Op.JUMPI(pc=Op.PUSH2[0xB7], condition=Op.EQ(0x2F54BF6E, Op.DUP1))
        + Op.JUMPI(pc=Op.PUSH2[0xE8], condition=Op.EQ(0x7065CB48, Op.DUP1))
        + Op.JUMPI(pc=0x105, condition=Op.EQ(0xB75C7DC6, Op.DUP1))
        + Op.JUMPI(pc=0x142, condition=Op.EQ(0xBA51A6DF, Op.DUP1))
        + Op.JUMPI(pc=0x15F, condition=Op.EQ(0xF00D4B5D, Op.DUP1))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH2[0x181]
        + Op.CALLDATALOAD(offset=0x4)
        + Op.PUSH1[0x0]
        + Op.PUSH1[0x40]
        + Op.PUSH1[0x0]
        + Op.CALLDATASIZE
        + Op.CALLDATACOPY(dest_offset=Op.DUP5, offset=Op.DUP3, size=Op.DUP1)
        + Op.SWAP1
        + Op.SWAP2
        + Op.SHA3
        + Op.SWAP1
        + Op.POP
        + Op.PUSH2[0x46D]
        + Op.DUP2
        + Op.JUMPDEST
        + Op.AND(Op.CALLER, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.PUSH1[0x0]
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.MSTORE(offset=0x20, value=0x102)
        + Op.SLOAD(key=Op.SHA3(offset=Op.DUP2, size=0x40))
        + Op.DUP2
        + Op.DUP1 * 2
        + Op.JUMPI(pc=0x58F, condition=Op.ISZERO(Op.EQ(Op.DUP2, Op.DUP4)))
        + Op.JUMP(pc=0x586)
        + Op.JUMPDEST
        + Op.PUSH2[0x187]
        + Op.CALLDATALOAD(offset=0x4)
        + Op.JUMPDEST
        + Op.PUSH20[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.AND
        + Op.PUSH1[0x0]
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.MSTORE(offset=0x20, value=0x102)
        + Op.SLOAD(key=Op.SHA3(offset=Op.DUP2, size=0x40))
        + Op.GT
        + Op.SWAP1
        + Op.JUMP
        + Op.JUMPDEST
        + Op.PUSH2[0x181]
        + Op.CALLDATALOAD(offset=0x4)
        + Op.PUSH1[0x40]
        + Op.PUSH1[0x0]
        + Op.CALLDATASIZE
        + Op.CALLDATACOPY(dest_offset=Op.DUP5, offset=Op.DUP3, size=Op.DUP1)
        + Op.SWAP1
        + Op.SWAP2
        + Op.SHA3
        + Op.SWAP1
        + Op.POP
        + Op.PUSH2[0x37C]
        + Op.DUP2
        + Op.JUMP(pc=Op.PUSH2[0x80])
        + Op.JUMPDEST
        + Op.PUSH2[0x181]
        + Op.CALLDATALOAD(offset=0x4)
        + Op.AND(Op.CALLER, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.PUSH1[0x0]
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.MSTORE(offset=0x20, value=0x102)
        + Op.SLOAD(key=Op.SHA3(offset=Op.DUP2, size=0x40))
        + Op.SWAP1
        + Op.DUP1 * 2
        + Op.JUMPI(pc=0x191, condition=Op.ISZERO(Op.EQ(Op.DUP2, Op.DUP4)))
        + Op.JUMP(pc=0x213)
        + Op.JUMPDEST
        + Op.PUSH2[0x181]
        + Op.CALLDATALOAD(offset=0x4)
        + Op.PUSH1[0x40]
        + Op.PUSH1[0x0]
        + Op.CALLDATASIZE
        + Op.CALLDATACOPY(dest_offset=Op.DUP5, offset=Op.DUP3, size=Op.DUP1)
        + Op.SWAP1
        + Op.SWAP2
        + Op.SHA3
        + Op.SWAP1
        + Op.POP
        + Op.PUSH2[0x533]
        + Op.DUP2
        + Op.JUMP(pc=Op.PUSH2[0x80])
        + Op.JUMPDEST
        + Op.PUSH2[0x181]
        + Op.CALLDATALOAD(offset=0x4)
        + Op.CALLDATALOAD(offset=0x24)
        + Op.PUSH1[0x0]
        + Op.PUSH1[0x40]
        + Op.PUSH1[0x0]
        + Op.CALLDATASIZE
        + Op.CALLDATACOPY(dest_offset=Op.DUP5, offset=Op.DUP3, size=Op.DUP1)
        + Op.SWAP1
        + Op.SWAP2
        + Op.SHA3
        + Op.SWAP1
        + Op.POP
        + Op.PUSH2[0x286]
        + Op.DUP2
        + Op.JUMP(pc=Op.PUSH2[0x80])
        + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.POP * 3
        + Op.PUSH1[0x0]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP3)
        + Op.MSTORE(offset=0x20, value=0x103)
        + Op.SHA3(offset=Op.DUP2, size=0x40)
        + Op.SLOAD(key=Op.ADD(Op.DUP2, 0x1))
        + Op.PUSH1[0x2]
        + Op.DUP5
        + Op.SWAP1
        + Op.EXP
        + Op.SWAP3
        + Op.SWAP1
        + Op.DUP4
        + Op.AND
        + Op.DUP2
        + Op.SWAP1
        + Op.JUMPI(pc=0x213, condition=Op.ISZERO(Op.GT))
        + Op.SLOAD(key=Op.DUP2)
        + Op.PUSH1[0x1]
        + Op.ADD(Op.DUP5, Op.DUP1)
        + Op.SLOAD(key=Op.DUP1)
        + Op.SWAP2
        + Op.SWAP1
        + Op.SWAP3
        + Op.SSTORE(key=Op.DUP5, value=Op.ADD)
        + Op.DUP5
        + Op.SWAP1
        + Op.SUB
        + Op.SWAP1
        + Op.SSTORE
        + Op.AND(Op.CALLER, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.PUSH1[0x40]
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.PUSH1[0x60]
        + Op.DUP7
        + Op.SWAP1
        + Op.MSTORE
        + Op.PUSH32[
            0xC7FB647E59B18047309AA15AAD418E5D7CA96D173AD704F1031A2C3D7591734B
        ]
        + Op.SWAP1
        + Op.DUP1
        + Op.LOG1
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.JUMP
        + Op.JUMPDEST
        + Op.ADD
        + Op.SSTORE
        + Op.PUSH20[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.AND(Op.DUP2, Op.DUP5)
        + Op.PUSH1[0x0]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
        + Op.MSTORE(offset=0x20, value=0x102)
        + Op.PUSH1[0x40]
        + Op.SHA3(offset=Op.DUP3, size=Op.DUP1)
        + Op.DUP3
        + Op.SWAP1
        + Op.SSTORE
        + Op.SWAP3
        + Op.DUP7
        + Op.AND
        + Op.MSTORE(offset=Op.DUP3, value=Op.DUP1)
        + Op.SWAP1
        + Op.DUP4
        + Op.SWAP1
        + Op.SHA3
        + Op.DUP6
        + Op.SWAP1
        + Op.SSTORE
        + Op.SWAP1
        + Op.DUP3
        + Op.MSTORE
        + Op.PUSH1[0x60]
        + Op.MSTORE
        + Op.PUSH32[
            0xB532073B38C83145E3E5135377A08BF9AAB55BC0FD7C1179CD4FB995D2A5159C
        ]
        + Op.SWAP1
        + Op.DUP1
        + Op.LOG1
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPDEST
        + Op.POP * 3
        + Op.JUMP
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x27F, condition=Op.ISZERO)
        + Op.PUSH2[0x294]
        + Op.DUP4
        + Op.JUMP(pc=Op.PUSH2[0xBE])
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x29F, condition=Op.ISZERO)
        + Op.POP
        + Op.JUMP(pc=0x281)
        + Op.JUMPDEST
        + Op.AND(Op.DUP5, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.PUSH1[0x0]
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.MSTORE(offset=0x20, value=0x102)
        + Op.SLOAD(key=Op.SHA3(offset=Op.DUP2, size=0x40))
        + Op.SWAP3
        + Op.POP
        + Op.DUP3
        + Op.JUMPI(pc=0x2D5, condition=Op.ISZERO(Op.EQ))
        + Op.POP
        + Op.JUMP(pc=0x281)
        + Op.JUMPDEST
        + Op.PUSH2[0x2F7]
        + Op.JUMPDEST
        + Op.SLOAD(key=0x104)
        + Op.PUSH1[0x0]
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x80C, condition=Op.ISZERO(Op.LT(Op.DUP2, Op.DUP2)))
        + Op.PUSH2[0x104]
        + Op.SLOAD(key=Op.DUP1)
        + Op.DUP3
        + Op.SWAP1
        + Op.DUP2
        + Op.JUMPI(pc=0x854, condition=Op.LT)
        + Op.STOP
        + Op.JUMPDEST
        + Op.AND(Op.DUP4, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.PUSH1[0x2]
        + Op.DUP4
        + Op.JUMPI(pc=0x21A, condition=Op.LT(Op.DUP2, 0x100))
        + Op.STOP
        + Op.JUMPDEST
        + Op.ADD
        + Op.SSTORE
        + Op.SLOAD(key=0x1)
        + Op.AND(Op.DUP4, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.PUSH1[0x0]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
        + Op.PUSH2[0x102]
        + Op.PUSH1[0x20]
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.PUSH1[0x40]
        + Op.SWAP2
        + Op.DUP3
        + Op.SWAP1
        + Op.SHA3
        + Op.SWAP4
        + Op.SWAP1
        + Op.SWAP4
        + Op.SSTORE
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.PUSH32[
            0x994A936646FE87FFE4F1E469D3D6AA417D6B855598397F323DE5B449F765F0C3
        ]
        + Op.SWAP2
        + Op.SWAP1
        + Op.LOG1
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMP
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x377, condition=Op.ISZERO)
        + Op.PUSH2[0x38A]
        + Op.DUP3
        + Op.JUMP(pc=Op.PUSH2[0xBE])
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x395, condition=Op.ISZERO)
        + Op.POP
        + Op.JUMP(pc=0x379)
        + Op.JUMPDEST
        + Op.PUSH2[0x39D]
        + Op.JUMP(pc=0x2D9)
        + Op.JUMPDEST
        + Op.SLOAD(key=0x1)
        + Op.PUSH1[0xFA]
        + Op.SWAP1
        + Op.JUMPI(pc=0x3B4, condition=Op.ISZERO(Op.ISZERO(Op.LT)))
        + Op.PUSH2[0x3B2]
        + Op.JUMP(pc=0x3CB)
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPDEST
        + Op.SLOAD(key=0x1)
        + Op.PUSH1[0xFA]
        + Op.SWAP1
        + Op.JUMPI(pc=0x3F5, condition=Op.ISZERO(Op.ISZERO(Op.LT)))
        + Op.POP
        + Op.JUMP(pc=0x379)
        + Op.JUMPDEST
        + Op.PUSH2[0x425]
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.PUSH1[0x1]
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x6F7, condition=Op.ISZERO(Op.LT(Op.DUP2, Op.SLOAD(key=0x1)))
        )
        + Op.JUMPDEST
        + Op.LT(Op.DUP2, Op.SLOAD(key=0x1))
        + Op.JUMPI(pc=0x753, condition=Op.ISZERO(Op.DUP1))
        + Op.POP
        + Op.PUSH1[0x2]
        + Op.DUP2
        + Op.JUMPI(pc=0x74C, condition=Op.LT(Op.DUP2, 0x100))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.ADD(Op.DUP2, Op.SLOAD(key=Op.DUP1))
        + Op.SWAP1
        + Op.DUP2
        + Op.SWAP1
        + Op.SSTORE
        + Op.AND(Op.DUP4, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.SWAP1
        + Op.PUSH1[0x2]
        + Op.SWAP1
        + Op.JUMPI(pc=0x31C, condition=Op.LT(Op.DUP2, 0x100))
        + Op.STOP
        + Op.JUMPDEST
        + Op.POP
        + Op.AND(Op.DUP4, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.PUSH1[0x40]
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.PUSH32[
            0x58619076ADF5BB0943D100EF88D52D7C3FD691B19D3A9071B555B651FBF418DA
        ]
        + Op.SWAP1
        + Op.PUSH1[0x20]
        + Op.SWAP1
        + Op.LOG1
        + Op.POP * 3
        + Op.JUMP
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x281, condition=Op.ISZERO)
        + Op.AND(Op.DUP4, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.PUSH1[0x0]
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.MSTORE(offset=0x20, value=0x102)
        + Op.SLOAD(key=Op.SHA3(offset=Op.DUP2, size=0x40))
        + Op.SWAP3
        + Op.POP
        + Op.DUP3
        + Op.JUMPI(pc=0x4A8, condition=Op.ISZERO(Op.EQ))
        + Op.POP
        + Op.JUMP(pc=0x377)
        + Op.JUMPDEST
        + Op.PUSH1[0x1] * 2
        + Op.POP(0x0)
        + Op.SLOAD
        + Op.SUB
        + Op.PUSH1[0x0]
        + Op.POP(0x0)
        + Op.SLOAD
        + Op.JUMPI(pc=0x4C3, condition=Op.ISZERO(Op.GT))
        + Op.POP
        + Op.JUMP(pc=0x377)
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.PUSH1[0x2]
        + Op.DUP4
        + Op.JUMPI(pc=0x4D3, condition=Op.LT(Op.DUP2, 0x100))
        + Op.STOP
        + Op.JUMPDEST
        + Op.ADD
        + Op.SSTORE
        + Op.AND(Op.DUP4, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.PUSH1[0x0]
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.MSTORE(offset=0x20, value=0x102)
        + Op.SHA3(offset=Op.DUP2, size=0x40)
        + Op.SSTORE
        + Op.PUSH2[0x3C7]
        + Op.JUMP(pc=0x2D9)
        + Op.JUMPDEST
        + Op.PUSH1[0x40]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP3)
        + Op.PUSH32[
            0xACBDB084C721332AC59F9B8E392196C9EB0E4932862DA8EB9BEAF0DAD4F550DA
        ]
        + Op.SWAP1
        + Op.PUSH1[0x20]
        + Op.SWAP1
        + Op.LOG1
        + Op.POP * 2
        + Op.JUMP
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x377, condition=Op.ISZERO)
        + Op.JUMPI(
            pc=0x548, condition=Op.ISZERO(Op.GT(Op.DUP3, Op.SLOAD(key=0x1)))
        )
        + Op.POP
        + Op.JUMP(pc=0x379)
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.DUP3
        + Op.SWAP1
        + Op.SSTORE
        + Op.PUSH2[0x504]
        + Op.JUMP(pc=0x2D9)
        + Op.JUMPDEST
        + Op.SSTORE(
            key=Op.DUP4,
            value=Op.ADD(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                Op.SLOAD(key=Op.DUP3),
            ),
        )
        + Op.ADD(Op.DUP4, 0x1)
        + Op.OR(Op.DUP3, Op.SLOAD(key=Op.DUP1))
        + Op.SWAP1
        + Op.SSTORE
        + Op.JUMPDEST
        + Op.POP * 4
        + Op.SWAP2
        + Op.SWAP1
        + Op.POP
        + Op.JUMP
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP7)
        + Op.MSTORE(offset=0x20, value=0x103)
        + Op.SHA3(offset=Op.DUP2, size=0x40)
        + Op.SLOAD(key=Op.DUP1)
        + Op.SWAP1
        + Op.SWAP5
        + Op.POP
        + Op.SWAP1
        + Op.SWAP3
        + Op.POP
        + Op.DUP3
        + Op.JUMPI(pc=0x61A, condition=Op.ISZERO(Op.EQ))
        + Op.SSTORE(key=Op.DUP4, value=Op.SLOAD(key=Op.DUP2))
        + Op.PUSH1[0x1]
        + Op.ADD(Op.DUP2, Op.DUP4)
        + Op.DUP4
        + Op.SWAP1
        + Op.SSTORE
        + Op.PUSH2[0x104]
        + Op.SLOAD(key=Op.DUP1)
        + Op.SWAP2
        + Op.DUP3
        + Op.ADD
        + Op.SSTORE(key=Op.DUP3, value=Op.DUP1)
        + Op.DUP3
        + Op.ISZERO(Op.DUP1)
        + Op.DUP3
        + Op.SWAP1
        + Op.JUMPI(pc=0x6A6, condition=Op.GT)
        + Op.MSTORE(offset=Op.DUP7, value=Op.DUP3)
        + Op.PUSH32[
            0x4C0BE60200FAA20559308CB7B5A1BB3255C16CB1CAB91F525B5AE7A03D02FABE
        ]
        + Op.SWAP1
        + Op.DUP2
        + Op.ADD
        + Op.SWAP1
        + Op.DUP3
        + Op.ADD
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x6A4, condition=Op.ISZERO(Op.GT(Op.DUP3, Op.DUP1)))
        + Op.SSTORE(key=Op.DUP2, value=0x0)
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.JUMP(pc=0x5F9)
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.SWAP2
        + Op.DUP3
        + Op.MSTORE
        + Op.PUSH1[0x20]
        + Op.SWAP1
        + Op.SWAP2
        + Op.SSTORE(key=Op.ADD, value=Op.SHA3)
        + Op.JUMPDEST
        + Op.POP
        + Op.SLOAD(key=Op.ADD(Op.DUP3, 0x1))
        + Op.PUSH1[0x2]
        + Op.DUP5
        + Op.SWAP1
        + Op.EXP
        + Op.SWAP1
        + Op.DUP2
        + Op.JUMPI(pc=0x586, condition=Op.ISZERO(Op.EQ(0x0, Op.AND)))
        + Op.AND(Op.CALLER, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.PUSH1[0x40]
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.PUSH1[0x60]
        + Op.DUP8
        + Op.SWAP1
        + Op.MSTORE
        + Op.PUSH32[
            0xE1C52DC63B719ADE82E8BEA94CC41A0D5D28E4AAF536ADB5E9CCCC9FF8C1AEDA
        ]
        + Op.SWAP1
        + Op.DUP1
        + Op.LOG1
        + Op.SLOAD(key=Op.DUP3)
        + Op.PUSH1[0x1]
        + Op.SWAP1
        + Op.JUMPI(pc=0x555, condition=Op.ISZERO(Op.ISZERO(Op.GT)))
        + Op.PUSH1[0x0]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP7)
        + Op.MSTORE(offset=0x20, value=0x103)
        + Op.PUSH2[0x104]
        + Op.SLOAD(key=Op.DUP1)
        + Op.PUSH1[0x40]
        + Op.SWAP1
        + Op.SWAP3
        + Op.SLOAD(key=Op.ADD(0x2, Op.SHA3))
        + Op.SWAP1
        + Op.SWAP2
        + Op.DUP2
        + Op.JUMPI(pc=0x6C0, condition=Op.LT)
        + Op.STOP
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPDEST
        + Op.POP * 3
        + Op.ADD(Op.DUP5, 0x2)
        + Op.DUP2
        + Op.SWAP1
        + Op.SSTORE
        + Op.PUSH2[0x104]
        + Op.SLOAD(key=Op.DUP1)
        + Op.DUP9
        + Op.SWAP3
        + Op.SWAP1
        + Op.DUP2
        + Op.JUMPI(pc=0x60D, condition=Op.LT)
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.SWAP2
        + Op.DUP3
        + Op.MSTORE
        + Op.PUSH1[0x20]
        + Op.SHA3(offset=Op.DUP4, size=Op.DUP1)
        + Op.SWAP1
        + Op.SWAP2
        + Op.ADD
        + Op.DUP3
        + Op.SWAP1
        + Op.SSTORE
        + Op.MSTORE(offset=Op.DUP3, value=Op.DUP8)
        + Op.PUSH2[0x103]
        + Op.SWAP1
        + Op.MSTORE
        + Op.SHA3(offset=Op.DUP2, size=0x40)
        + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)
        + Op.PUSH1[0x1]
        + Op.ADD(Op.DUP2, Op.DUP2)
        + Op.DUP4
        + Op.SWAP1
        + Op.SSTORE
        + Op.PUSH1[0x2]
        + Op.SWAP1
        + Op.SWAP2
        + Op.ADD
        + Op.SWAP2
        + Op.SWAP1
        + Op.SWAP2
        + Op.SSTORE
        + Op.SWAP5
        + Op.POP
        + Op.JUMP(pc=0x586)
        + Op.JUMPDEST
        + Op.POP
        + Op.SWAP1
        + Op.JUMP
        + Op.JUMPDEST
        + Op.EQ(0x0, Op.SLOAD(key=Op.ADD))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x760, condition=Op.ISZERO)
        + Op.PUSH1[0x1]
        + Op.ADD(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
            Op.SLOAD(key=Op.DUP1),
        )
        + Op.SWAP1
        + Op.SSTORE
        + Op.JUMPDEST
        + Op.GT(Op.SLOAD(key=Op.DUP1), 0x1)
        + Op.JUMPI(pc=0x701, condition=Op.ISZERO(Op.DUP1))
        + Op.POP
        + Op.SLOAD(key=0x1)
        + Op.PUSH1[0x2]
        + Op.SWAP1
        + Op.JUMPI(pc=0x6FB, condition=Op.LT(Op.DUP2, 0x100))
        + Op.STOP
        + Op.JUMPDEST
        + Op.ISZERO(Op.EQ(0x0, Op.SLOAD(key=Op.ADD)))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x72F, condition=Op.ISZERO)
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.JUMP(pc=0x3DB)
        + Op.JUMPDEST
        + Op.LT(Op.DUP2, Op.SLOAD(key=0x1))
        + Op.JUMPI(pc=0x784, condition=Op.ISZERO(Op.DUP1))
        + Op.POP
        + Op.SLOAD(key=0x1)
        + Op.PUSH1[0x2]
        + Op.SWAP1
        + Op.JUMPI(pc=0x77D, condition=Op.LT(Op.DUP2, 0x100))
        + Op.STOP
        + Op.JUMPDEST
        + Op.ISZERO(Op.EQ(0x0, Op.SLOAD(key=Op.ADD)))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x79F, condition=Op.ISZERO(Op.DUP1))
        + Op.POP
        + Op.PUSH1[0x2]
        + Op.DUP2
        + Op.JUMPI(pc=0x799, condition=Op.LT(Op.DUP2, 0x100))
        + Op.STOP
        + Op.JUMPDEST
        + Op.EQ(0x0, Op.SLOAD(key=Op.ADD))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x7B8, condition=Op.ISZERO)
        + Op.SLOAD(key=0x1)
        + Op.PUSH1[0x2]
        + Op.SWAP1
        + Op.JUMPI(pc=0x7BD, condition=Op.LT(Op.DUP2, 0x100))
        + Op.STOP
        + Op.JUMPDEST
        + Op.ADD
        + Op.SSTORE
        + Op.JUMPDEST
        + Op.JUMP(pc=0x3D0)
        + Op.JUMPDEST
        + Op.SLOAD(key=Op.ADD)
        + Op.PUSH1[0x2]
        + Op.DUP3
        + Op.JUMPI(pc=0x7CD, condition=Op.LT(Op.DUP2, 0x100))
        + Op.STOP
        + Op.JUMPDEST
        + Op.ADD
        + Op.SSTORE
        + Op.DUP1
        + Op.PUSH2[0x102]
        + Op.PUSH1[0x0]
        + Op.PUSH1[0x2]
        + Op.DUP4
        + Op.JUMPI(pc=0x7E3, condition=Op.LT(Op.DUP2, 0x100))
        + Op.STOP
        + Op.JUMPDEST
        + Op.MSTORE(offset=Op.DUP2, value=Op.SLOAD(key=Op.ADD))
        + Op.ADD(Op.DUP2, 0x20)
        + Op.SWAP2
        + Op.SWAP1
        + Op.SWAP2
        + Op.MSTORE
        + Op.PUSH1[0x40]
        + Op.ADD
        + Op.PUSH1[0x0]
        + Op.SWAP1
        + Op.DUP2
        + Op.SHA3
        + Op.SWAP2
        + Op.SWAP1
        + Op.SWAP2
        + Op.SSTORE
        + Op.SLOAD(key=0x1)
        + Op.PUSH1[0x2]
        + Op.SWAP1
        + Op.JUMPI(pc=0x7B5, condition=Op.LT(Op.DUP2, 0x100))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH2[0x104]
        + Op.SLOAD(key=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.SSTORE(key=Op.DUP4, value=Op.DUP1)
        + Op.SWAP2
        + Op.SWAP1
        + Op.SWAP2
        + Op.MSTORE
        + Op.PUSH32[
            0x4C0BE60200FAA20559308CB7B5A1BB3255C16CB1CAB91F525B5AE7A03D02FABE
        ]
        + Op.SWAP1
        + Op.DUP2
        + Op.ADD
        + Op.SWAP1
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x27F, condition=Op.ISZERO(Op.GT(Op.DUP3, Op.DUP1)))
        + Op.SSTORE(key=Op.DUP2, value=0x0)
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.JUMP(pc=0x840)
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.SWAP2
        + Op.DUP3
        + Op.MSTORE
        + Op.JUMPI(
            pc=0x8A6,
            condition=Op.ISZERO(
                Op.ISZERO(
                    Op.EQ(
                        Op.SLOAD(key=Op.ADD),
                        Op.SHA3(offset=Op.DUP3, size=0x20),
                    )
                )
            ),
        )
        + Op.PUSH2[0x104]
        + Op.SLOAD(key=Op.DUP1)
        + Op.PUSH2[0x103]
        + Op.SWAP2
        + Op.PUSH1[0x0]
        + Op.SWAP2
        + Op.DUP5
        + Op.SWAP1
        + Op.DUP2
        + Op.JUMPI(pc=0x87C, condition=Op.LT)
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.SWAP2
        + Op.DUP3
        + Op.MSTORE
        + Op.PUSH1[0x20]
        + Op.SHA3(offset=Op.DUP4, size=Op.DUP1)
        + Op.SWAP1
        + Op.SWAP2
        + Op.MSTORE(offset=Op.DUP4, value=Op.SLOAD(key=Op.ADD))
        + Op.DUP3
        + Op.ADD
        + Op.SWAP3
        + Op.SWAP1
        + Op.SWAP3
        + Op.MSTORE
        + Op.PUSH1[0x40]
        + Op.SHA3(offset=Op.DUP2, size=Op.ADD)
        + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)
        + Op.ADD(Op.DUP2, 0x1)
        + Op.DUP3
        + Op.SWAP1
        + Op.SSTORE
        + Op.SSTORE(key=Op.ADD, value=0x2)
        + Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.JUMP(pc=0x2E0),
        storage={
            0: 1,
            1: 2,
            3: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
            4: 0x3FB1CD2CD96C6D5C0B5EB3322D807B34482481D4,
            0x6E369836487C234B9E553EF3F787C2D8865520739D340C67B3D251A33986E58D: 1,  # noqa: E501
            0xD3E69D8C7F41F7AEAF8130DDC53047AEEE8CB46A73D6BAE86B7E7D6BF8312E6B: 2,  # noqa: E501
        },
        balance=100,
        nonce=0,
        address=Address(0x6295EE1B4F6DD65047762F924ECD367C17EABF8F),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A75EF08F, nonce=1)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes("173825d9") + Hash(sender, left_padding=True),
        gas_limit=10000000,
        value=100,
        nonce=1,
    )

    post = {
        contract_0: Account(
            storage={
                0: 1,
                1: 1,
                3: 0x3FB1CD2CD96C6D5C0B5EB3322D807B34482481D4,
                0xD3E69D8C7F41F7AEAF8130DDC53047AEEE8CB46A73D6BAE86B7E7D6BF8312E6B: 1,  # noqa: E501
            },
            code=bytes.fromhex(
                "7c01000000000000000000000000000000000000000000000000000000006000350463173825d981146100655780632f54bf6e146100b75780637065cb48146100e8578063b75c7dc614610105578063ba51a6df14610142578063f00d4b5d1461015f57005b6101816004356000604060003680828437909120905061046d815b73ffffffffffffffffffffffffffffffffffffffff3316600090815261010260205260408120548180808381141561058f57610586565b6101876004355b73ffffffffffffffffffffffffffffffffffffffff16600090815261010260205260408120541190565b610181600435604060003680828437909120905061037c81610080565b61018160043573ffffffffffffffffffffffffffffffffffffffff3316600090815261010260205260408120549080808381141561019157610213565b610181600435604060003680828437909120905061053381610080565b6101816004356024356000604060003680828437909120905061028681610080565b60006000f35b8060005260206000f35b5050506000828152610103602052604081206001810154600284900a929083168190111561021357815460018084018054919092018455849003905573ffffffffffffffffffffffffffffffffffffffff3316604090815260608690527fc7fb647e59b18047309aa15aad418e5d7ca96d173ad704f1031a2c3d7591734b9080a15b5050505050565b015573ffffffffffffffffffffffffffffffffffffffff84811660008181526101026020526040808220829055928616808252908390208590559082526060527fb532073b38c83145e3e5135377a08bf9aab55bc0fd7c1179cd4fb995d2a5159c9080a15b505b505050565b1561027f57610294836100be565b1561029f5750610281565b73ffffffffffffffffffffffffffffffffffffffff84166000908152610102602052604081205492508214156102d55750610281565b6102f75b6101045460005b8181101561080c5761010480548290811061085457005b73ffffffffffffffffffffffffffffffffffffffff8316600283610100811061021a57005b015560015473ffffffffffffffffffffffffffffffffffffffff831660008181526101026020908152604091829020939093559081527f994a936646fe87ffe4f1e469d3d6aa417d6b855598397f323de5b449f765f0c39190a15b505b50565b156103775761038a826100be565b156103955750610379565b61039d6102d9565b60015460fa901015156103b4576103b26103cb565b505b60015460fa901015156103f55750610379565b6104255b600060015b6001548110156106f7575b600154811080156107535750600281610100811061074c57005b6001805481019081905573ffffffffffffffffffffffffffffffffffffffff831690600290610100811061031c57005b5073ffffffffffffffffffffffffffffffffffffffff831660409081527f58619076adf5bb0943d100ef88d52d7c3fd691b19d3a9071b555b651fbf418da90602090a1505050565b156102815773ffffffffffffffffffffffffffffffffffffffff83166000908152610102602052604081205492508214156104a85750610377565b60016001600050540360006000505411156104c35750610377565b600060028361010081106104d357005b015573ffffffffffffffffffffffffffffffffffffffff8316600090815261010260205260408120556103c76102d9565b60408281527facbdb084c721332ac59f9b8e392196c9eb0e4932862da8eb9beaf0dad4f550da90602090a15050565b15610377576001548211156105485750610379565b60008290556105046102d9565b82547fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff018355600183018054821790555b50505050919050565b600086815261010360205260408120805490945090925082141561061a5781548355600183810183905561010480549182018082558280158290116106a6578286527f4c0be60200faa20559308cb7b5a1bb3255c16cb1cab91f525b5ae7a03d02fabe9081019082015b808211156106a457600081556001016105f9565b6000918252602090912001555b506001820154600284900a908116600014156105865773ffffffffffffffffffffffffffffffffffffffff3316604090815260608790527fe1c52dc63b719ade82e8bea94cc41a0d5d28e4aaf536adb5e9cccc9ff8c1aeda9080a182546001901115156105555760008681526101036020526101048054604090922060020154909181106106c057005b505b505050600284018190556101048054889290811061060d57005b6000918252602080832090910182905587825261010390526040812081815560018181018390556002909101919091559450610586565b5090565b01546000145b1561076057600180547fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0190555b60018054118015610701575060015460029061010081106106fb57005b0154600014155b1561072f576001016103db565b600154811080156107845750600154600290610100811061077d57005b0154600014155b801561079f5750600281610100811061079957005b01546000145b156107b85760015460029061010081106107bd57005b01555b6103d0565b015460028261010081106107cd57005b015580610102600060028361010081106107e357005b01548152602081019190915260400160009081209190915560015460029061010081106107b557005b61010480546000808355919091527f4c0be60200faa20559308cb7b5a1bb3255c16cb1cab91f525b5ae7a03d02fabe908101905b8082111561027f5760008155600101610840565b60009182526020822001541415156108a6576101048054610103916000918490811061087c57005b60009182526020808320909101548352820192909252604001812081815560018101829055600201555b6001016102e056"  # noqa: E501
            ),
            balance=200,
            nonce=0,
        ),
        sender: Account(storage={}, nonce=2),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
