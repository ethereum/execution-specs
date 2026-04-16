"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stCreateTest/CreateCollisionResultsFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateCollisionResultsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_collision_results(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x8AF6A7AF30D840BA137E8F3F34D54CFB8BEBA6E2)
    contract_1 = Address(0x40F1299359EA754AC29EB2662A1900752BF8275F)
    contract_2 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4294967296,
    )

    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: lll
    # {
    #   [[0]] 0x001D
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1D) + Op.STOP,
        storage={0: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x8AF6A7AF30D840BA137E8F3F34D54CFB8BEBA6E2),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[0]] 0x001D
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1D) + Op.STOP,
        storage={0: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x40F1299359EA754AC29EB2662A1900752BF8275F),  # noqa: E501
    )
    # Source: lll
    # {
    #   ; Variables are 0x20 bytes (= 256 bits) apart, except for
    #   ; code buffers that get 0x100 (256 bytes)
    #   (def 'creation          0x100)
    #   (def 'contractCode      0x200)
    #   (def 'constructorCode   0x300)
    #   (def 'contractLength    0x520)
    #   (def 'constructorLength 0x540)
    #   (def 'addr1             0x600)
    #   (def 'callRet           0x640)
    #   (def 'buffer            0x660)
    #   ; Addresses of the contracts (to check what code is there)
    #   (def 'OrigAddr1 0x8af6a7af30d840ba137e8f3f34d54cfb8beba6e2)
    #   (def 'OrigAddr2 0x40f1299359ea754ac29eb2662a1900752bf8275f)
    #   ; Other constants
    #   (def 'NOP 0)   ; No OPeration
    #   ; Understand the input.
    #   [creation]       (shr $ 0 248)
    #   ; Code for created contract
    #   (def 'contractMacro
    #       (lll
    #          (sstore 0 0xFF)
    #          contractCode
    #       )
    #   )
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Create the contract and a constructor to pass to CREATE[2]
    #   ;
    #   [constructorLength]
    #     (lll
    # ... (43 more lines)
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x100,
            value=Op.DIV(Op.CALLDATALOAD(offset=0x0), Op.EXP(0x2, 0xF8)),
        )
        + Op.PUSH1[0x15]
        + Op.CODECOPY(dest_offset=0x300, offset=0x158, size=Op.DUP1)
        + Op.PUSH2[0x540]
        + Op.MSTORE
        + Op.PUSH1[0x6]
        + Op.CODECOPY(dest_offset=0x200, offset=0x16D, size=Op.DUP1)
        + Op.PUSH2[0x520]
        + Op.MSTORE
        + Op.JUMPI(
            pc=Op.PUSH2[0x49], condition=Op.EQ(Op.MLOAD(offset=0x100), 0x1)
        )
        + Op.MSTORE(
            offset=0x600,
            value=Op.CREATE2(
                value=0x0,
                offset=0x300,
                size=Op.MLOAD(offset=0x540),
                salt=0x5A17,
            ),
        )
        + Op.JUMP(pc=Op.PUSH2[0x58])
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
        + Op.SSTORE(key=0x11, value=Op.MLOAD(offset=0x600))
        + Op.MSTORE(
            offset=0x640,
            value=Op.CALL(
                gas=0xFFFF,
                address=contract_0,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x21, value=Op.PC)
        + Op.SSTORE(key=0x12, value=Op.SUB(Op.MLOAD(offset=0x640), 0x1))
        + Op.SSTORE(key=0x13, value=Op.RETURNDATASIZE)
        + Op.MSTORE(
            offset=0x640,
            value=Op.CALL(
                gas=0xFFFF,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x22, value=Op.PC)
        + Op.SSTORE(key=0x14, value=Op.SUB(Op.MLOAD(offset=0x640), 0x1))
        + Op.SSTORE(key=0x15, value=Op.RETURNDATASIZE)
        + Op.SSTORE(key=0x30, value=Op.EXTCODESIZE(address=contract_0))
        + Op.EXTCODECOPY(
            address=contract_0,
            dest_offset=0x660,
            offset=0x0,
            size=Op.SLOAD(key=0x30),
        )
        + Op.SSTORE(key=0x31, value=Op.MLOAD(offset=0x660))
        + Op.SSTORE(key=0x32, value=Op.EXTCODESIZE(address=contract_1))
        + Op.EXTCODECOPY(
            address=contract_1,
            dest_offset=0x660,
            offset=0x0,
            size=Op.SLOAD(key=0x32),
        )
        + Op.SSTORE(key=0x33, value=Op.MLOAD(offset=0x660))
        + Op.STOP
        + Op.INVALID
        + Op.PUSH1[0x6]
        + Op.CODECOPY(dest_offset=0x200, offset=0xF, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + Op.SSTORE(key=0x0, value=0xFF)
        + Op.STOP
        + Op.SSTORE(key=0x0, value=0xFF)
        + Op.STOP,
        storage={
            16: 24743,
            17: 24743,
            18: 24743,
            19: 24743,
            20: 24743,
            21: 24743,
            32: 24743,
            33: 24743,
            34: 24743,
        },
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )

    tx_data = [
        Bytes("01"),
        Bytes("02"),
    ]
    tx_gas = [16777216]

    tx = Transaction(
        sender=sender,
        to=contract_2,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {
        contract_2: Account(
            storage={
                32: 89,
                33: 143,
                34: 200,
                48: 6,
                49: 0x601D600055000000000000000000000000000000000000000000000000000000,  # noqa: E501
                50: 6,
                51: 0x601D600055000000000000000000000000000000000000000000000000000000,  # noqa: E501
            },
        ),
        contract_0: Account(
            storage={0: 29}, code=bytes.fromhex("601d60005500")
        ),
        contract_1: Account(
            storage={0: 29}, code=bytes.fromhex("601d60005500")
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
